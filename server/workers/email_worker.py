from shared_lib.infra.redis import redis_client
import json
from shared_lib.pydantic_models.models import EmailJob
from shared_lib.Email import VerificationEmail,SMTPEmailSender

STREAM = "rag:sendmail-jobs"
GROUP = "rag-sendmail-workers"
CONSUMER = "email-worker-1"
sender = SMTPEmailSender()

async def consume_email_jobs():
    while True:
        try:
            response = await redis_client.xreadgroup(
                groupname=GROUP,
                consumername=CONSUMER,
                streams={
                    STREAM: ">"
                },
                count=10,
                block=5000
            )
            if not response:
                continue
            for stream, messages in response:
                for message_id, message in messages:
                    try:
                        job_string = message['job']
                        job_dict:EmailJob = json.loads(job_string)

                        print(job_dict)
                        
                        token = job_dict['token']
                        email_address = job_dict['email_address']
                        type = job_dict['type']
                        

                        if(type == 'forgot-password'):
                            pass
                        
                        if(type == 'verification'):
                            email = VerificationEmail(token)
                            sender.send(email_template=email,recipient=email_address)

                        # processor.process_job(job_dict)
                        await redis_client.xack(
                            STREAM,
                            GROUP,
                            message_id
                        )
                    except Exception as e:
                        print(f"Job failed: {e}")
        except Exception as e:
            print(e)
            print('An exception occurred')

if __name__ == "__main__":
    import sys
    import asyncio
    try:
        asyncio.run(consume_email_jobs())
    except KeyboardInterrupt:
        print("\n[!] Keystroke 'Ctrl+C' detected! Cleaning up resources...")
        sys.exit(0)