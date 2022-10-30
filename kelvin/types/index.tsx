type TextParam = {
  kind: "TextParam";
  name: string;
  value: string | null;
  label: string;
};

type IntParam = {
  kind: "IntParam";
  name: string;
  value: string | null;
  label: string;
};

type IdParam = {
  kind: "IdParam";
  name: string;
  value: string | null;
  label: string;
};

type ActionParam = TextParam | IntParam | IdParam;

type Action = {
  kind: string;
  params: ActionParam[];
  label: string;
};

type TextRow = {
  id: string;
  text: string;
};

type TextCard = {
  kind: "TextCard";
  id: string;
  rows: TextRow[];
};

type PaperRow = {
  id: string;
  title: string | null;
  authors: string[];
  year: number | null;
  citations: number | null;
  raw_data: Record<string, any>;
};

type PaperCard = {
  kind: "PaperCard";
  id: string;
  rows: PaperRow[];
};

type ActionCard = {
  kind: "ActionCard";
  id: string;
  rows: Action[];
};

type Card = TextCard | ActionCard | PaperCard;

type CardView = {
  card_id: string;
  selected_rows: { [row_id: string]: boolean };
};

type CardWithView = {
  card: Card;
  view: CardView;
};

type Workspace = {
  cards: Card[];
  view: CardView;
  available_actions: Action[];
};
