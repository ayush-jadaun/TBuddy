"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const HyperspeedBackground = () => {
  return (
    <div className="absolute inset-0 pointer-events-none opacity-30">
      <div className="w-full h-full bg-gradient-to-br from-red-900/10 via-black to-amber-900/10" />
    </div>
  );
};

const ChatMessage = ({ message, isUser }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      <div
        className={`max-w-[80%] p-4 rounded-2xl ${
          isUser
            ? "bg-gradient-to-r from-red-700 to-red-900 text-white"
            : "bg-zinc-900/60 border border-zinc-800 text-zinc-100"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {message.timestamp && (
          <p className="text-xs opacity-60 mt-2">
            {new Date(message.timestamp).toLocaleTimeString()}
          </p>
        )}
      </div>
    </motion.div>
  );
};

const StreamingIndicator = ({ message }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start mb-4"
    >
      <div className="max-w-[80%] p-4 rounded-2xl bg-zinc-900/60 border border-amber-500/30">
        <div className="flex items-center gap-2">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-4 h-4 border-2 border-amber-500/30 border-t-amber-500 rounded-full"
          />
          <p className="text-zinc-300 text-sm">{message}</p>
        </div>
      </div>
    </motion.div>
  );
};

const AgentStatusCard = ({ agent, status, progress }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "text-green-400 border-green-500/30 bg-green-500/5";
      case "processing":
        return "text-yellow-400 border-yellow-500/30 bg-yellow-500/5";
      case "pending":
        return "text-zinc-500 border-zinc-700";
      case "timeout":
      case "failed":
        return "text-red-400 border-red-500/30 bg-red-500/5";
      default:
        return "text-zinc-500 border-zinc-700";
    }
  };

  const agentIcons = {
    weather: "🌤️",
    events: "🎉",
    maps: "🗺️",
    budget: "💰",
    itinerary: "✨",
    orchestrator: "🎯",
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`p-3 rounded-lg border ${getStatusColor(status)}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{agentIcons[agent] || "🤖"}</span>
          <span className="text-sm font-medium capitalize">{agent}</span>
        </div>
        <span className="text-xs uppercase font-semibold">{status}</span>
      </div>
      {status === "processing" && (
        <div className="mt-2 w-full bg-zinc-800 rounded-full h-1">
          <motion.div
            animate={{ x: ["-100%", "100%"] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
            className="h-1 bg-amber-500 rounded-full w-1/3"
          />
        </div>
      )}
    </motion.div>
  );
};

const ResultCard = ({ title, data, icon }) => {
  if (!data) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 mb-3"
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">{icon}</span>
        <h4 className="text-lg font-semibold text-zinc-100">{title}</h4>
      </div>
      <div className="text-zinc-300 text-sm">
        {typeof data === "string" ? (
          <p>{data}</p>
        ) : (
          <pre className="whitespace-pre-wrap overflow-x-auto max-h-96 bg-zinc-950/50 p-3 rounded">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
    </motion.div>
  );
};

const TravelChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [agentStatuses, setAgentStatuses] = useState({});
  const [progressPercent, setProgressPercent] = useState(0);
  const [results, setResults] = useState({});

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage, agentStatuses]);

  const connectWebSocket = (sessionId) => {
    return new Promise((resolve, reject) => {
      if (wsRef.current) {
        wsRef.current.close();
      }

      console.log("🔌 Connecting WebSocket to session:", sessionId);
      const ws = new WebSocket(
        `ws://localhost:8000/api/v2/orchestrator/ws/${sessionId}`
      );

      ws.onopen = () => {
        console.log("✅ WebSocket connected");
        setIsConnected(true);
        resolve(ws);
      };

      ws.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          console.log("📨 WebSocket update:", update);

          switch (update.type) {
            case "connected":
              setStreamingMessage("Connected to travel planning system...");
              if (update.context) {
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content: `Continuing your trip to ${update.context.destination}`,
                    timestamp: update.timestamp,
                  },
                ]);
              }
              break;

            case "agent_start":
              // Agent started processing
              setAgentStatuses((prev) => ({
                ...prev,
                [update.agent]: "processing",
              }));
              setStreamingMessage(update.message);
              console.log(`🚀 ${update.agent} started`);
              break;

            case "progress":
              setStreamingMessage(update.message);
              if (update.progress_percent) {
                setProgressPercent(update.progress_percent);
              }
              break;

            case "agent_update":
              // Agent completed successfully
              if (update.agent) {
                setAgentStatuses((prev) => ({
                  ...prev,
                  [update.agent]: "completed",
                }));
                console.log(`✅ ${update.agent} completed`);
              }
              setStreamingMessage(update.message);

              // Store agent data
              if (update.data) {
                setResults((prev) => ({ ...prev, ...update.data }));
              }
              break;

            case "completed":
              setStreamingMessage("");
              setIsProcessing(false);
              setProgressPercent(100);

              // Add final results message
              const resultSummary = [];
              if (update.data?.weather_data) resultSummary.push("Weather");
              if (update.data?.events_data) resultSummary.push("Events");
              if (update.data?.maps_data) resultSummary.push("Routes");
              if (update.data?.budget_data) resultSummary.push("Budget");
              if (update.data?.itinerary_data) resultSummary.push("Itinerary");

              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  content: `✅ Travel plan complete! Generated: ${resultSummary.join(
                    ", "
                  )}`,
                  timestamp: update.timestamp,
                },
              ]);

              if (update.data) {
                setResults(update.data);
              }
              break;

            case "error":
              setStreamingMessage("");
              if (update.agent) {
                setAgentStatuses((prev) => ({
                  ...prev,
                  [update.agent]: "failed",
                }));
              }
              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  content: `❌ Error: ${update.message}`,
                  timestamp: update.timestamp,
                },
              ]);
              break;

            case "timeout":
              setIsConnected(false);
              setStreamingMessage("");
              break;
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        setIsConnected(false);
        setStreamingMessage("");
        reject(error);
      };

      ws.onclose = () => {
        console.log("🔌 WebSocket disconnected");
        setIsConnected(false);
      };

      wsRef.current = ws;
    });
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userInput = input;
    setInput("");
    setIsProcessing(true);
    setStreamingMessage("Connecting...");
    setAgentStatuses({});
    setProgressPercent(0);
    setResults({});

    try {
      // Generate or use existing session ID
      const newSessionId =
        sessionId ||
        `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      console.log("📝 Using session ID:", newSessionId);

      if (!sessionId) {
        setSessionId(newSessionId);
      }

      // CRITICAL: Connect WebSocket FIRST and wait for connection
      console.log("🔌 Connecting WebSocket...");
      await connectWebSocket(newSessionId);

      // Small delay to ensure WebSocket is fully ready
      await new Promise((resolve) => setTimeout(resolve, 300));

      console.log("📤 Starting travel plan generation...");
      setStreamingMessage("Initiating workflow...");

      // Send request to async endpoint (returns immediately)
      const response = await fetch(
        "http://localhost:8000/api/v2/orchestrator/plan",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: userInput,
            session_id: newSessionId,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process query");
      }

      const result = await response.json();
      console.log("✅ Workflow started:", result);
      console.log("🎧 Listening for real-time updates via WebSocket...");

      setStreamingMessage("Workflow started - processing agents...");
    } catch (error) {
      console.error("❌ Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `❌ Failed to process your request: ${error.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
      setIsProcessing(false);
      setStreamingMessage("");
      if (wsRef.current) {
        wsRef.current.close();
      }
    }
  };

  const handleNewConversation = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setMessages([]);
    setSessionId(null);
    setIsConnected(false);
    setIsProcessing(false);
    setStreamingMessage("");
    setAgentStatuses({});
    setProgressPercent(0);
    setResults({});
  };

  return (
    <div className="min-h-screen w-screen overflow-x-hidden bg-black relative">
      <HyperspeedBackground />
      <div className="bg-black/60 inset-0 absolute" />

      <div className="relative z-10 flex flex-col h-screen">
        {/* Header */}
        <div className="sticky top-0 backdrop-blur-xl bg-black/80 border-b border-zinc-800 px-4 py-4">
          <div className="max-w-6xl mx-auto flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-light text-zinc-100">
                Travel Chat Assistant
              </h1>
              <p className="text-sm text-zinc-400 mt-1">
                {sessionId
                  ? `Session: ${sessionId.slice(0, 15)}...`
                  : "New conversation"}
                {isConnected && (
                  <span className="ml-2 text-green-400">● Connected</span>
                )}
              </p>
            </div>
            <button
              onClick={handleNewConversation}
              className="px-4 py-2 bg-zinc-800/50 hover:bg-zinc-700/50 border border-zinc-700 rounded-lg text-zinc-300 transition-all"
            >
              New Chat
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-4xl mx-auto">
            <AnimatePresence>
              {messages.map((msg, idx) => (
                <ChatMessage
                  key={idx}
                  message={msg}
                  isUser={msg.role === "user"}
                />
              ))}

              {isProcessing && streamingMessage && (
                <StreamingIndicator message={streamingMessage} />
              )}

              {/* Progress Bar */}
              {isProcessing && progressPercent > 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mb-4"
                >
                  <div className="w-full bg-zinc-800 rounded-full h-2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${progressPercent}%` }}
                      transition={{ duration: 0.3 }}
                      className="h-2 bg-gradient-to-r from-red-600 to-amber-500 rounded-full"
                    />
                  </div>
                  <p className="text-xs text-zinc-500 mt-1 text-center">
                    {progressPercent}% complete
                  </p>
                </motion.div>
              )}

              {/* Agent Status Cards */}
              {Object.keys(agentStatuses).length > 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4"
                >
                  {Object.entries(agentStatuses).map(([agent, status]) => (
                    <AgentStatusCard
                      key={agent}
                      agent={agent}
                      status={status}
                      progress={progressPercent}
                    />
                  ))}
                </motion.div>
              )}

              {/* Results */}
              {results.weather_data && (
                <ResultCard
                  title="Weather Forecast"
                  data={results.weather_data}
                  icon="🌤️"
                />
              )}
              {results.events_data && (
                <ResultCard
                  title="Local Events"
                  data={results.events_data}
                  icon="🎉"
                />
              )}
              {results.maps_data && (
                <ResultCard
                  title="Route Information"
                  data={results.maps_data}
                  icon="🗺️"
                />
              )}
              {results.budget_data && (
                <ResultCard
                  title="Budget Breakdown"
                  data={results.budget_data}
                  icon="💰"
                />
              )}
              {results.itinerary_data && (
                <ResultCard
                  title="Your Itinerary"
                  data={results.itinerary_data}
                  icon="✨"
                />
              )}
            </AnimatePresence>

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="sticky bottom-0 backdrop-blur-xl bg-black/80 border-t border-zinc-800 px-4 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Ask about your travel plans..."
                disabled={isProcessing}
                className="flex-1 bg-zinc-900/50 border border-zinc-700 rounded-xl px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-amber-400/50 focus:ring-2 focus:ring-amber-400/20 disabled:opacity-50"
              />
              <button
                onClick={handleSendMessage}
                disabled={!input.trim() || isProcessing}
                className="px-6 py-3 bg-gradient-to-r from-red-700 to-red-900 hover:from-red-600 hover:to-red-700 disabled:from-zinc-800 disabled:to-zinc-800 text-white rounded-xl transition-all disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isProcessing ? "Processing..." : "Send"}
              </button>
            </div>
            <p className="text-xs text-zinc-500 mt-2">
              💡 Try: "Plan a 3-day trip to Paris" or "Change my budget to
              $2000"
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TravelChatPage;
