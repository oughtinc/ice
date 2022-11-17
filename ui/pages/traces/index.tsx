import Link from "next/link";
import {useEffect, useState} from "react";

export default function TraceListPage() {
  const [traces, setTraces] = useState<string[]>([]);
  useEffect(() => {
    fetch("/api/traces/")
      .then(res => res.json())
      .then(setTraces);
  }, []);
  return (
    <div className="m-8 flex flex-col space-y-4">
      {traces.map(traceId => (
        <Link key={traceId} className="font-mono" href={`/traces/${traceId}`}>
          {traceId}
        </Link>
      ))}
    </div>
  );
}
