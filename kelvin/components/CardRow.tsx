const CardRow = ({ cardKind, row }) => {
  if (cardKind == "TextCard") {
    return <span>{row.text}</span>;
  } else if (cardKind == "PaperCard") {
    const hasFullText = row?.raw_data?.body?.value?.paragraphs?.length;
    return (
      <div>
        {hasFullText ? "📰" : ""} {row.title} ({row.year})
      </div>
    );
  } else {
    return <pre>{JSON.stringify(row, null, 2)}</pre>;
  }
};

export default CardRow;
