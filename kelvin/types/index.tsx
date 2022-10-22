export type ActionParam = {
  name: string;
  kind: "text_param";
  value: string | null;
};

export type Action = {
  kind: "question_action";
  params: ActionParam[];
};

export type Card<T> = {
  kind: string;
  rows: T[];
};

export type TextCard = Card<string> & {
  kind: "text_card";
};

export type ActionCard = Card<Action> & {
  kind: "action_card";
};

export type Workspace = {
  cards: { [string]: Card };
  currentCardId: string;
};
