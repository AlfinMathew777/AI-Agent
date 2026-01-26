export default function Home() {
  return (
    <div className="page">
      <h1>Welcome to Southern Horizons Hotel</h1>
      <p className="subtitle">
        AI Concierge & Staff Knowledge Assistant
      </p>

      <section className="info-section">
        <h2>About This Project</h2>
        <p>
          This tool demonstrates how AI can transform hospitality by providing 
          fast, accurate answers to both guests and staff. It is designed as a 
          modern, easy-to-use front end connected to a FastAPI backend and a 
          future Retrieval-Augmented Generation (RAG) system.
        </p>
      </section>

      <section className="info-section">
        <h2>What You Can Do</h2>
        <ul>
          <li>💁‍♂️ Guest Concierge – Ask general hotel FAQs, local area info, amenities, and services.</li>
          <li>🧑‍🍳 Staff Assistant – Ask about internal procedures, service standards, and training notes.</li>
          <li>⚙️ Powered by FastAPI – Clean, modern backend ready for AI and document search.</li>
        </ul>
      </section>

      <section className="info-section">
        <h2>How It Works</h2>
        <p>
          Each section sends your question to a dedicated API endpoint. Later steps 
          will connect this interface to a full AI model combined with real hotel 
          knowledge (RAG system).
        </p>
      </section>

      <footer className="footer">
        Demo project · SHHG AI Concierge & Staff Assistant
      </footer>
    </div>
  );
}