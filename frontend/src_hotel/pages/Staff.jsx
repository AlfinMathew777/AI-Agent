import ChatBox from "../components/ChatBox";

export default function Staff() {
  return (
    <div className="page">
      <h1>Staff Knowledge Assistant</h1>
      <p>
        Internal tool for staff. Ask about procedures, service standards, and training information.
      </p>

      <ChatBox endpoint="http://127.0.0.1:8000/ask/staff" />
    </div>
  );
}