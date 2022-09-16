import OpenAPIClientAxios from "openapi-client-axios";
import { useEffect, useState } from "react";
import { Client } from "../client";

if (!process.env.NEXT_PUBLIC_API_HOST)
  throw new Error("NEXT_PUBLIC_API_HOST environment variable must be defined");
const api = new OpenAPIClientAxios({
  definition: `${process.env.NEXT_PUBLIC_API_HOST}/openapi.json`,
  axiosConfigDefaults: {
    baseURL: process.env.NEXT_PUBLIC_API_HOST,
  },
});

const useApi = () => {
  const [client, setClient] = useState<Promise<Client> | undefined>();

  useEffect(() => {
    (async () => {
      setClient(api.getClient<Client>());
    })();
  }, []);

  return client;
};

export default useApi;
