import axios, { type Method } from "axios";

const BASE_URL = import.meta.env.VITE_API_URL;

export const apiCall = async (
  endpoint: string,
  body: any = {},
  method: Method = "GET",
  headers: Record<string, string> = {}
) => {
  try {
    const response = await axios({
      url: `${BASE_URL}${endpoint}`,
      method,
      data: body,
      headers: {
        "Content-Type": "application/json",
        ...headers,
      },
    });

    return response.data;
  } catch (error: any) {
    console.error("API Error:", error?.response?.data || error.message);
    throw error;
  }
};