import { readdir } from "fs/promises";
import { GetServerSideProps } from "next";
import Link from "next/link";
import { basename, extname } from "path";

export const getServerSideProps: GetServerSideProps = async () => {
  let filenames: string[] = [];
  try {
    filenames = await readdir("public/traces");
  } catch {}

  const traceIds = filenames.flatMap(filename => {
    const ext = extname(filename);
    return ext === ".jsonl" ? [basename(filename, ext)] : [];
  });

  return { props: { traceIds } };
};

export default function TraceListPage({ traceIds }: { traceIds: string[] }) {
  return (
    <div className="m-8 flex flex-col space-y-4">
      {traceIds.map(traceId => (
        <Link key={traceId} className="font-mono" href={`/traces/${traceId}`}>
          {traceId}
        </Link>
      ))}
    </div>
  );
}
