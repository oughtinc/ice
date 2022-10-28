import React from "react";

const Error = ({ error }: { error: Error }) => {
  return <div className="flex justify-center items-center h-screen">{error}</div>;
};

export default Error;
