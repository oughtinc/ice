// Paper:

/* {
 *   "id": "2KCCPiIPuUsDwxqr",
 *   "title": "Impact of social media on the trait of empathy",
 *   "authors": [
 *     "Naveli Sharma",
 *     "Shravya Gupta",
 *     "S. Seth."
 *   ],
 *   "year": 2020,
 *   "citations": 1,
 *   "raw_data": {
 *     "sddocname": "work",
 *     "documentid": "id:work:work::55eb0250159d881e77892fe95d5ed8c2cac4f0a5",
 *     "title": "Impact of social media on the trait of empathy",
 *     "abstract": "With steady rise in the use of social networking sites, Changes in the behavior of people are evident, especially in the psychological characteristic or trait of empathy. The current study is a quantitative study which explores two variables, i.e. the influence of SNS (Independent Variable) and empathy (Dependent Variable). For the fulfillment of the aim, a total of 100 responses were recorded and the data was compared between two groups, i.e. Male and Female. The age of the sample ranges from 18 to 40. The data was collected by using Davis’s Interpersonal Reactivity Index which scores on four constructs (empathetic concern, personal distress, fantasy, perspective taking) and the questionnaire was distributed through the medium of various social media apps and sites such Facebook, WhatsApp, Instagram, and Others. The data was compared by dividing it into two categories, i.e. usage of SNS for less or more hours. Furthermore, T-test was applied to check the same. Thus, our study laid a groundwork for understanding empathy’s role in facilitating interactions on social media.",
 *     "publicationYear": 2020,
 *     "doi": "10.25215/0801.121",
 *     "magId": 3033785729,
 *     "ssId": "55eb0250159d881e77892fe95d5ed8c2cac4f0a5",
 *     "citedByCount": 1,
 *     "authors": [
 *       {
 *         "ssId": "2000240358",
 *         "name": "Naveli Sharma"
 *       },
 *       {
 *         "ssId": "1751679152",
 *         "name": "Shravya Gupta"
 *       },
 *       {
 *         "ssId": "151220868",
 *         "name": "S. Seth."
 *       }
 *     ],
 *     "id": "55eb0250159d881e77892fe95d5ed8c2cac4f0a5"
 *   }
 * } */

const PaperRow = ({ row }) => {
  return (
    <div className="p-2">
      <div className="font-semibold">{row.title}</div>
      <div>
        <span className="text-gray-600">{row.year}</span>{" "}
        <span className="text-gray-400">{row.authors.join(", ")}</span>
      </div>
    </div>
  );
};

const TextRow = ({ row }) => {
  return <span>{row.text}</span>;
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
    default:
      return <UnknownRow row={row} />;
  }
};

export default CardRow;
