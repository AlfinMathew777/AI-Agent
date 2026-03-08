import ChatBox from "../components/ChatBox";

export default function Guest() {
  return (
    <div className="page">
      <h1>Guest Concierge</h1>
      <p>
        Ask general questions about hotel amenities, check-in times, local attractions, and more.
      </p>

      <ChatBox endpoint="http://127.0.0.1:8000/ask/guest" />
    </div>
  );
}