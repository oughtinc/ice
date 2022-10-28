type TextParam = {
  name: string;
  kind: "text_param";
  value: string | null;
};

type IntParam = {
  name: string;
  kind: "int_param";
  value: string | null;
};

type ActionParam = TextParam | IntParam;

type AddTextRowAction = {
  kind: "add_text_row_action";
  params: TextParam[];
};

type EditTextRowAction = {
  kind: "edit_text_row_action";
  params: [TextParam, IntParam];
};

type Action = AddTextRowAction | EditTextRowAction;

type TextCard = {
  id: string;
  kind: "text_card";
  rows: string[];
};

type ActionCard = {
  id: string;
  kind: "action_card";
  rows: Action[];
};

type Card = TextCard | ActionCard;

type CardView = {
  card_id: string;
  selected_row_index: number | null;
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
