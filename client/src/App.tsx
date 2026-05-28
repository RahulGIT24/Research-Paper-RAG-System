import { useEffect } from "react";
import { SignIn } from "./pages/SignIn";
import { apiCall } from "./lib/api";

function App() {
  useEffect(() => {
    (async () => {
      const res = await apiCall("/user/");
      console.log(res);
    })();
  }, []);
  return (
    <>
      <SignIn />
    </>
  );
}

export default App;
