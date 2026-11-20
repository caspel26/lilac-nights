import { useState, type ReactNode } from "react";

interface ButtonProps {
  label: string;
  onPress?: () => void;
  children?: ReactNode;
}

export function Button({ label, onPress, ...rest }: ButtonProps) {
  return (
    <button type="button" className="btn" onClick={onPress} {...rest}>
      {label}
    </button>
  );
}

export default function Counter(props: { start: number }) {
  const [count, setCount] = useState(props.start);
  const x = () => setCount(count + 1);
  return (
    <div className="counter" {...props}>
      <Button label={`Count: ${count}`} onClick={x} />
      <span>{count > 0 ? "positive" : "zero"}</span>
    </div>
  );
}
