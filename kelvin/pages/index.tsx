import Head from "next/head";
import { useEffect, useState } from "react";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8935";

export default function HomePage() {
  const [examples, setExamples] = useState<string[]>([]);
  useEffect(() => {
    fetch(`${backendUrl}/kelvin/examples/list`)
      .then(res => res.json())
      .then(examples => {
        setExamples(examples);
      });
  }, []);

  return (
    <div className="m-8">
      <Head>
        <title>Kelvin</title>
      </Head>
      <p>Kelvin</p>
      <pre>{examples.join("\n")}</pre>
    </div>
  );
}
