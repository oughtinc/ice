import { useEffect, useRef, useState } from "react";

const ActionForm = ({ partialAction, onSubmit }) => {
  const { kind, params, label } = partialAction;
  const [formValues, setFormValues] = useState({});
  const firstInputRef = useRef(null); // create a ref to store the first input

  useEffect(() => {
    if (firstInputRef.current) {
      // if the ref is assigned, focus it
      firstInputRef.current.focus();
    }
  }, []); // run only once after the first render

  const handleChange = (name, value) => {
    setFormValues(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = e => {
    e.preventDefault();
    const missingValues = params.filter(param => param.value === null && !formValues[param.name]);
    if (missingValues.length > 0) {
      console.error("Missing values for", missingValues.map(param => param.label).join(", "));
      return;
    }
    // Create full action from partial action and form values
    const action = {
      ...partialAction,
      params: params.map(param => ({
        ...param,
        value: formValues[param.name] || param.value,
      })),
    };
    // Submit
    onSubmit(action);
  };

  const renderParam = (param, index) => {
    const { name, kind, value, label } = param;
    if (value !== null) {
      // skip the param if it already has a value
      return null;
    }
    switch (kind) {
      case "TextParam":
        return (
          <div key={name} className="mb-4">
            <label htmlFor={name} className="block text-sm font-medium text-gray-700">
              {label}
            </label>
            <input
              type="text"
              id={name}
              name={name}
              value={formValues[name] || ""}
              onChange={e => handleChange(name, e.target.value)}
              className="mt-1 block w-full border border-gray-300 py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              ref={index === 0 ? firstInputRef : null} // assign the ref to the first input
            />
          </div>
        );
      case "IntParam":
        return (
          <div key={name} className="mb-4">
            <label htmlFor={name} className="block text-sm font-medium text-gray-700">
              {label}
            </label>
            <input
              type="number"
              id={name}
              name={name}
              value={formValues[name] || ""}
              onChange={e => handleChange(name, e.target.value)}
              className="mt-1 block w-full border border-gray-300 py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              ref={index === 0 ? firstInputRef : null} // assign the ref to the first input
            />
          </div>
        );
      case "IdParam":
        return (
          <div key={name} className="mb-4">
            <label htmlFor={name} className="block text-sm font-medium text-gray-700">
              {label}
            </label>
            <input
              type="text"
              id={name}
              name={name}
              value={formValues[name] || ""}
              onChange={e => handleChange(name, e.target.value)}
              className="mt-1 block w-full border border-gray-300 py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              readOnly // assume id_param is read-only
              ref={index === 0 ? firstInputRef : null} // assign the ref to the first input
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="action-form bg-white p-6 max-w-md mx-auto">
      <h3 className="text-gray-900 mb-4">{label}</h3>
      <form onSubmit={handleSubmit}>
        {params.map(renderParam)}
        <button
          type="submit"
          className="w-full bg-blue-150 py-2 px-4 hover:bg-blue-200 focus:bg-blue-200 focus:outline-none"
        >
          Run
        </button>
      </form>
    </div>
  );
};

export default ActionForm;
