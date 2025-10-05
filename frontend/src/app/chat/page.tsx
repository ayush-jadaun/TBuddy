"use client";
import React, { useState, useRef, useEffect } from "react";
import { Send, Loader2, CheckCircle, XCircle, RotateCcw } from "lucide-react";

// Types
interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface CollectedInfo {
  destination?: string;
  origin?: string;
  travel_dates?: string[];
  travelers_count?: number;
  budget_range?: string;
  user_preferences?: {
    interests?: string[];
    pace?: string;
    dietary_restrictions?: string[];
  };
}

interface ChatResponse {
  session_id: string;
  message: string;
  stage: string;
  collected_info: CollectedInfo;
  missing_fields: string[];
  is_ready: boolean;
  suggestions?: string[];
}

interface TripPlanResponse {
  success: boolean;
  message: string;
  session_id: string;
  trip_plan_status?: string;
  data?: any;
  error?: string;
}

const API_BASE_URL = "http://localhost:8000/api/v1/chat";

export default function TravelChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [collectedInfo, setCollectedInfo] = useState<CollectedInfo>({});
  const [stage, setStage] = useState("greeting");
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [isReadyToPlan, setIsReadyToPlan] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tripPlan, setTripPlan] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      // Update session ID if new
      if (!sessionId) {
        setSessionId(data.session_id);
      }

      // Add assistant message
      const assistantMessage: Message = {
        role: "assistant",
        content: data.message,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Update state
      setCollectedInfo(data.collected_info);
      setStage(data.stage);
      setMissingFields(data.missing_fields);
      setIsReadyToPlan(data.is_ready);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      console.error("Error sending message:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const confirmAndPlan = async () => {
    if (!sessionId || !isReadyToPlan) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          confirmed: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: TripPlanResponse = await response.json();

      if (data.success) {
        setTripPlan(data.data);
        const successMessage: Message = {
          role: "assistant",
          content: `🎉 ${data.message}\n\nYour trip plan has been created! Check the Trip Plan section below.`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, successMessage]);
      } else {
        throw new Error(data.error || "Failed to create trip plan");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to confirm trip");
      console.error("Error confirming trip:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = async () => {
    if (!sessionId) {
      // Just reset local state
      setMessages([]);
      setCollectedInfo({});
      setStage("greeting");
      setMissingFields([]);
      setIsReadyToPlan(false);
      setTripPlan(null);
      return;
    }

    try {
      await fetch(`${API_BASE_URL}/session/${sessionId}`, {
        method: "DELETE",
      });
    } catch (err) {
      console.error("Error resetting conversation:", err);
    }

    // Reset all state
    setMessages([]);
    setSessionId("");
    setCollectedInfo({});
    setStage("greeting");
    setMissingFields([]);
    setIsReadyToPlan(false);
    setError(null);
    setTripPlan(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6">
            <h1 className="text-3xl font-bold">Travel Planning Assistant</h1>
            <p className="text-blue-100 mt-2">
              Let&apos;s plan your perfect trip together!
            </p>
            {sessionId && (
              <p className="text-sm text-blue-200 mt-1">
                Session: {sessionId.substring(0, 20)}...
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
            {/* Chat Section */}
            <div className="lg:col-span-2 flex flex-col h-[600px]">
              <div className="flex-1 overflow-y-auto bg-gray-50 rounded-lg p-4 mb-4 space-y-4">
                {messages.length === 0 && (
                  <div className="text-center text-gray-500 mt-8">
                    <p className="text-lg">
                      👋 Hi! I&apos;m your travel planning assistant.
                    </p>
                    <p className="mt-2">
                      Tell me where you&apos;d like to go, and I&apos;ll help plan your
                      trip!
                    </p>
                  </div>
                )}

                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-4 ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-white border border-gray-200"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      <p
                        className={`text-xs mt-2 ${
                          msg.role === "user"
                            ? "text-blue-100"
                            : "text-gray-400"
                        }`}
                      >
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Error Display */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 flex items-start">
                  <XCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}

              {/* Input Area */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  disabled={isLoading}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-5 h-5" />
                </button>
                <button
                  onClick={resetConversation}
                  className="bg-gray-200 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-300 transition-colors"
                  title="Reset conversation"
                >
                  <RotateCcw className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Info Sidebar */}
            <div className="space-y-4">
              {/* Stage */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-2">
                  Conversation Stage
                </h3>
                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  {stage}
                </span>
              </div>

              {/* Collected Information */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-800 mb-3">
                  Collected Information
                </h3>
                <div className="space-y-2 text-sm">
                  {collectedInfo.destination && (
                    <div className="flex items-start">
                      <CheckCircle className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium">Destination:</span>
                        <p className="text-gray-600">
                          {collectedInfo.destination}
                        </p>
                      </div>
                    </div>
                  )}
                  {collectedInfo.origin && (
                    <div className="flex items-start">
                      <CheckCircle className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium">Origin:</span>
                        <p className="text-gray-600">{collectedInfo.origin}</p>
                      </div>
                    </div>
                  )}
                  {collectedInfo.travel_dates && (
                    <div className="flex items-start">
                      <CheckCircle className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium">Dates:</span>
                        <p className="text-gray-600">
                          {collectedInfo.travel_dates.join(" to ")}
                        </p>
                      </div>
                    </div>
                  )}
                  {collectedInfo.travelers_count && (
                    <div className="flex items-start">
                      <CheckCircle className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium">Travelers:</span>
                        <p className="text-gray-600">
                          {collectedInfo.travelers_count}
                        </p>
                      </div>
                    </div>
                  )}
                  {collectedInfo.budget_range && (
                    <div className="flex items-start">
                      <CheckCircle className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium">Budget:</span>
                        <p className="text-gray-600">
                          {collectedInfo.budget_range}
                        </p>
                      </div>
                    </div>
                  )}
                  {Object.keys(collectedInfo).length === 0 && (
                    <p className="text-gray-400 italic">
                      No information collected yet
                    </p>
                  )}
                </div>
              </div>

              {/* Missing Fields */}
              {missingFields.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-semibold text-yellow-800 mb-2">
                    Still Need
                  </h3>
                  <ul className="space-y-1 text-sm">
                    {missingFields.map((field, idx) => (
                      <li key={idx} className="text-yellow-700">
                        • {field.replace(/_/g, " ")}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Confirm Button */}
              {isReadyToPlan && (
                <button
                  onClick={confirmAndPlan}
                  disabled={isLoading}
                  className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-semibold"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <Loader2 className="w-5 h-5 animate-spin mr-2" />
                      Planning...
                    </span>
                  ) : (
                    "✈️ Confirm & Plan Trip"
                  )}
                </button>
              )}

              {/* Trip Plan Result */}
              {tripPlan && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-semibold text-green-800 mb-2">
                    Trip Plan Created!
                  </h3>
                  <pre className="text-xs bg-white p-3 rounded overflow-auto max-h-64">
                    {JSON.stringify(tripPlan, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
