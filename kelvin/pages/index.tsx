import Head from "next/head";
import CurrentCard from "../components/CurrentCard";
import useWorkspace from "../hooks/useWorkspace";

export default function HomePage() {
  const { workspace, loading, error } = useWorkspace();

  return (
    <div className="m-8">
      <Head>
        <title>Kelvin</title>
      </Head>
      {loading && <p>Loading...</p>}
      {error && <p>Error: {error.message}</p>}
      {!loading && workspace && <CurrentCard workspace={workspace} />}
    </div>
  );
}
