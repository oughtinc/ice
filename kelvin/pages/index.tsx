import Head from "next/head";
import Workspace from "/components/Workspace";

export default function HomePage() {
  return (
    <div className="m-8">
      <Head>
        <title>Kelvin</title>
      </Head>
      <Workspace />
    </div>
  );
}
