const PaperRow = ({ row }) => {
  return (
    <div className="p-2">
      <div className="font-semibold">{row.title}</div>
      <div>
        <span className="text-gray-600">{row.year}</span>{" "}
        <span className="text-gray-400">{row.authors.join(", ")}</span>
        {row.has_full_text ? " [Full text]" : ""}
      </div>
      {row.is_expanded && (
        <div className="text-sm text-gray-600">
          <div>{row.citations} citations</div>
          <div>DOI {row.raw_data.doi}</div>
        </div>
      )}
    </div>
  );
};

const TextRow = ({ row }) => {
  return <span>{row.text}</span>;
};

const PaperSectionRow = ({ row }) => {
  return (
    <div className="p-2">
      <div className="font-semibold">{row.title}</div>
      <div className="text-sm text-gray-600">
        {row.is_expanded
          ? row.paragraphs.map((paragraph, i) => <span key={i}>{paragraph}</span>)
          : row.preview}
      </div>
    </div>
  );
};

const UnknownRow = ({ row }) => {
  return <pre>{JSON.stringify(row, null, 2)}</pre>;
};

const CardRow = ({ row }) => {
  switch (row.kind) {
    case "Text":
      return <TextRow row={row} />;
    case "Paper":
      return <PaperRow row={row} />;
    case "PaperSection":
      return <PaperSectionRow row={row} />;
    default:
      return <UnknownRow row={row} />;
  }
};

export default CardRow;
