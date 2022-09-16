import React, { useRef } from "react";

type SeparatorProps = {
  detailWidth: number;
  setDetailWidth: (width: number) => void;
};

const Separator = ({ detailWidth, setDetailWidth }: SeparatorProps) => {
  // Ref for the initial mouse position and width when dragging starts
  const dragRef = useRef({ x: 0, width: 0 });

  // Mouse event handlers for the separator div
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    dragRef.current.x = e.clientX;
    dragRef.current.width = detailWidth;
    document.addEventListener("mousemove", handleMouseMove as any);
    document.addEventListener("mouseup", handleMouseUp as any);
  };

  // Calculate the new width based on the mouse position and the ref
  // values and update the state
  const handleMouseMove = (e: MouseEvent) => {
    const delta = e.clientX - dragRef.current.x;
    const newWidth = dragRef.current.width - delta;
    setDetailWidth(newWidth);
  };

  const handleMouseUp = () => {
    document.removeEventListener("mousemove", handleMouseMove as any);
    document.removeEventListener("mouseup", handleMouseUp as any);
  };

  return <div className="w-1 bg-gray-100 cursor-col-resize" onMouseDown={handleMouseDown}></div>;
};

export default Separator;
