import { ActionParam } from "../types";

type Props = {
  param: ActionParam;
  onChange: (value: string | null) => void; // callback for updating the parameter value
};

const Param = ({ param, onChange }: Props) => {
  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value || null);
  };

  return (
    <span className="bg-white px-2 py-1 rounded-md border border-gray-300">
      {`${param.name}: `}
      {param.kind == "text_param" ? (
        <input
          type="text"
          placeholder={`Enter ${param.name}`}
          value={param.value || ""}
          onChange={handleInputChange}
        />
      ) : (
        <span>{`${param.value} (${param.kind})`}</span>
      )}
    </span>
  );
};

export default Param;
