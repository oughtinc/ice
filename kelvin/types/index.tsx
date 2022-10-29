type TextParam = {
  name: string;
  kind: "text_param";
  value: string | null;
  label: string;
};

type IntParam = {
  name: string;
  kind: "int_param";
  value: string | null;
  label: string;
};

type IdParam = {
  name: string;
  kind: "id_param";
  value: string | null;
  label: string;
};

type ActionParam = TextParam | IntParam | IdParam;

type AddTextRowAction = {
  kind: "add_text_row_action";
  params: TextParam[];
  label: string;
};

type EditTextRowAction = {
  kind: "edit_text_row_action";
  params: [TextParam, IdParam];
  label: string;
};

type Action = AddTextRowAction | EditTextRowAction;

type TextRow = {
  id: string;
  text: string;
};

type TextCard = {
  id: string;
  kind: "text_card";
  rows: TextRow[];
};

type ActionCard = {
  id: string;
  kind: "action_card";
  rows: Action[];
};

type Card = TextCard | ActionCard;

type CardView = {
  card_id: string;
  selected_rows: { [row_id: string]: boolean };
  available_actions: Action[];
};

type CardWithView = {
  card: Card;
  view: CardView;
};

type Workspace = {
  cards: Card[];
  view: CardView;
};
