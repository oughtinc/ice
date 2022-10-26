type TextParam = {
  name: string;
  kind: "text_param";
  value: string | null;
};

type QuestionAction = {
  kind: "create_question_action";
  params: TextParam[];
};

type Action = QuestionAction;

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

type Workspace = {
  cards: (TextCard | ActionCard)[];
  currentCardId: string;
};
