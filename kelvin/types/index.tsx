type TextParam = {
  name: string;
  kind: "text_param";
  value: string | null;
};

type AddQuestionAction = {
  kind: "add_question_action";
  params: TextParam[];
};

type Action = AddQuestionAction;

type Card<T> = {
  id: string;
  kind: string;
  rows: T[];
};

type TextCard = Card<string> & {
  kind: "text_card";
};

type ActionCard = Card<Action> & {
  kind: "action_card";
};

type CardView = {
  card_id: string;
  selected_row_index: number | null;
  available_actions: Action[];
};

type Workspace = {
  cards: Card<any>[];
  view: CardView;
};

type CardWithView = {
  card: Card<any>;
  view: CardView;
};
