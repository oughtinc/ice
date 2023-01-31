import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function TraceListPage() {
  const [traces, setTraces] = useState<string[]>([]);
  useEffect(() => {
    fetch("/api/traces/")
      .then(res => res.json())
      .then(setTraces);
  }, []);
  return traces.length === 0 ? (
    <div className="m-8">
      No traces yet! Create your first one by following the&nbsp;
      <a href="https://primer.ought.org/chapters/hello-world">Hello World</a>
      &nbsp;example in the Primer.
    </div>
  ) : (
    <div className="m-8 flex flex-col space-y-4">
      {traces.map(traceId => (
        <Link key={traceId} className="font-mono" to={traceId}>
          {traceId}
        </Link>
      ))}
    </div>
  );
}
