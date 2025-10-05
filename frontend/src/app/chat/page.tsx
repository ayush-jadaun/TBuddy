"use client";
import { useState, useEffect, memo } from "react";
import { motion, AnimatePresence } from "framer-motion";

const HyperspeedBackground = memo(function HyperspeedBackground() {
  return (
    <div className="absolute inset-0 pointer-events-none opacity-30">
      <div className="w-full h-full bg-gradient-to-br from-red-900/10 via-black to-amber-900/10" />
    </div>
  );
});

const titles = [
  "Where planning is Spontaneous",
  "Less Google, More Goggles",
  "Plan less, Chill more",
];

const TravelPlannerForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    destination: "",
    origin: "",
    travel_dates: ["", ""],
    travelers_count: 1,
    budget_range: "",
    interests: [],
    pace: "moderate",
    dietary_restrictions: [],
    accessibility_needs: [],
    group_type: "solo",
  });

  const interestOptions = [
    "art",
    "food",
    "history",
    "nature",
    "adventure",
    "culture",
    "shopping",
    "nightlife",
  ];
  const dietaryOptions = [
    "vegetarian",
    "vegan",
    "gluten-free",
    "halal",
    "kosher",
    "none",
  ];
  const accessibilityOptions = [
    "wheelchair",
    "visual",
    "hearing",
    "mobility",
    "none",
  ];

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleDateChange = (index, value) => {
    const newDates = [...formData.travel_dates];
    newDates[index] = value;
    setFormData((prev) => ({ ...prev, travel_dates: newDates }));
  };

  const addDate = () => {
    setFormData((prev) => ({
      ...prev,
      travel_dates: [...prev.travel_dates, ""],
    }));
  };

  const removeDate = (index) => {
    if (formData.travel_dates.length > 2) {
      const newDates = formData.travel_dates.filter((_, i) => i !== index);
      setFormData((prev) => ({ ...prev, travel_dates: newDates }));
    }
  };

  const toggleMultiSelect = (field, value) => {
    setFormData((prev) => {
      const current = prev[field];
      const newValue = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      return { ...prev, [field]: newValue };
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const validDates = formData.travel_dates.filter((d) => d !== "");
    if (validDates.length < 1) {
      alert("Please add at least one travel date");
      return;
    }

    const payload = {
      destination: formData.destination,
      origin: formData.origin,
      travel_dates: validDates,
      travelers_count: formData.travelers_count,
      budget_range: formData.budget_range || undefined,
      user_preferences: {
        interests:
          formData.interests.length > 0 ? formData.interests : undefined,
        pace: formData.pace,
        dietary_restrictions: formData.dietary_restrictions.filter(
          (d) => d !== "none"
        ),
        accessibility_needs: formData.accessibility_needs.filter(
          (a) => a !== "none"
        ),
        group_type: formData.group_type,
      },
    };

    onSubmit(payload);
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      className="w-full max-w-4xl mx-auto p-8 bg-black/40 backdrop-blur-md border border-zinc-800/50 rounded-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h2 className="text-3xl font-light text-zinc-100 mb-8 text-center">
        Plan Your Journey
      </h2>

      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              Origin <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.origin}
              onChange={(e) => handleChange("origin", e.target.value)}
              className="w-full bg-zinc-900/50 border border-zinc-700 rounded-lg p-3 text-zinc-100 focus:outline-none focus:border-amber-400/50 focus:ring-2 focus:ring-amber-400/20"
              placeholder="e.g., New York, USA"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              Destination <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.destination}
              onChange={(e) => handleChange("destination", e.target.value)}
              className="w-full bg-zinc-900/50 border border-zinc-700 rounded-lg p-3 text-zinc-100 focus:outline-none focus:border-amber-400/50 focus:ring-2 focus:ring-amber-400/20"
              placeholder="e.g., Paris, France"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-2">
            Travel Dates <span className="text-red-500">*</span>
          </label>
          <div className="space-y-2">
            {formData.travel_dates.map((date, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="date"
                  value={date}
                  onChange={(e) => handleDateChange(index, e.target.value)}
                  className="flex-1 bg-zinc-900/50 border border-zinc-700 rounded-lg p-3 text-zinc-100 focus:outline-none focus:border-amber-400/50"
                />
                {formData.travel_dates.length > 2 && (
                  <button
                    type="button"
                    onClick={() => removeDate(index)}
                    className="px-3 bg-red-900/50 hover:bg-red-900/70 border border-red-800 rounded-lg text-zinc-300 transition-colors"
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addDate}
            className="mt-2 text-sm text-amber-400 hover:text-amber-300 transition-colors"
          >
            + Add another date
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              Number of Travelers <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min="1"
              max="20"
              required
              value={formData.travelers_count}
              onChange={(e) =>
                handleChange("travelers_count", parseInt(e.target.value))
              }
              className="w-full bg-zinc-900/50 border border-zinc-700 rounded-lg p-3 text-zinc-100 focus:outline-none focus:border-amber-400/50"
            />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              Budget Range (Optional)
            </label>
            <input
              type="text"
              value={formData.budget_range}
              onChange={(e) => handleChange("budget_range", e.target.value)}
              className="w-full bg-zinc-900/50 border border-zinc-700 rounded-lg p-3 text-zinc-100 focus:outline-none focus:border-amber-400/50"
              placeholder="e.g., $1000-2000"
            />
          </div>
        </div>

        <div className="pt-6 border-t border-zinc-800">
          <h3 className="text-xl font-light text-zinc-100 mb-4">
            Preferences (Optional)
          </h3>

          <div className="mb-6">
            <label className="block text-sm text-zinc-400 mb-2">
              Interests
            </label>
            <div className="flex flex-wrap gap-2">
              {interestOptions.map((interest) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleMultiSelect("interests", interest)}
                  className={`px-4 py-2 rounded-full text-sm transition-all ${
                    formData.interests.includes(interest)
                      ? "bg-amber-600 text-white border-amber-500"
                      : "bg-zinc-800/50 text-zinc-300 border-zinc-700 hover:border-amber-400"
                  } border`}
                >
                  {interest}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm text-zinc-400 mb-2">
                Travel Pace
              </label>
              <select
                value={formData.pace}
                onChange={(e) => handleChange("pace", e.target.value)}
                className="w-full bg-zinc-900/50 border border-zinc-700 rounded-lg p-3 text-zinc-100 focus:outline-none focus:border-amber-400/50"
              >
                <option value="relaxed">Relaxed</option>
                <option value="moderate">Moderate</option>
                <option value="packed">Packed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-zinc-400 mb-2">
                Group Type
              </label>
              <select
                value={formData.group_type}
                onChange={(e) => handleChange("group_type", e.target.value)}
                className="w-full bg-zinc-900/50 border border-zinc-700 rounded-lg p-3 text-zinc-100 focus:outline-none focus:border-amber-400/50"
              >
                <option value="solo">Solo</option>
                <option value="couple">Couple</option>
                <option value="family">Family</option>
                <option value="friends">Friends</option>
              </select>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm text-zinc-400 mb-2">
              Dietary Restrictions
            </label>
            <div className="flex flex-wrap gap-2">
              {dietaryOptions.map((dietary) => (
                <button
                  key={dietary}
                  type="button"
                  onClick={() =>
                    toggleMultiSelect("dietary_restrictions", dietary)
                  }
                  className={`px-4 py-2 rounded-full text-sm transition-all ${
                    formData.dietary_restrictions.includes(dietary)
                      ? "bg-red-600 text-white border-red-500"
                      : "bg-zinc-800/50 text-zinc-300 border-zinc-700 hover:border-red-400"
                  } border`}
                >
                  {dietary}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm text-zinc-400 mb-2">
              Accessibility Needs
            </label>
            <div className="flex flex-wrap gap-2">
              {accessibilityOptions.map((access) => (
                <button
                  key={access}
                  type="button"
                  onClick={() =>
                    toggleMultiSelect("accessibility_needs", access)
                  }
                  className={`px-4 py-2 rounded-full text-sm transition-all ${
                    formData.accessibility_needs.includes(access)
                      ? "bg-blue-600 text-white border-blue-500"
                      : "bg-zinc-800/50 text-zinc-300 border-zinc-700 hover:border-blue-400"
                  } border`}
                >
                  {access}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="w-full bg-gradient-to-r from-red-700 to-red-900 hover:from-red-600 hover:to-red-700 text-white py-4 rounded-xl transition-all duration-300 shadow-lg hover:shadow-red-500/50 text-lg font-medium mt-8"
        >
          Generate Travel Plan
        </button>
      </div>
    </motion.form>
  );
};

const LoadingState = ({ agentStatus }) => {
  const agents = [
    { key: "weather", label: "Checking weather conditions", icon: "🌤️" },
    { key: "events", label: "Finding local events", icon: "🎉" },
    { key: "maps", label: "Calculating best routes", icon: "🗺️" },
    { key: "budget", label: "Calculating your budget", icon: "💰" },
    { key: "itinerary", label: "Crafting your perfect itinerary", icon: "✨" },
  ];

  return (
    <div className="flex flex-col items-center justify-center space-y-8 min-h-screen">
      <motion.div
        className="relative"
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      >
        <div className="w-20 h-20 border-4 border-red-900/30 border-t-red-500 rounded-full" />
      </motion.div>

      <div className="w-full max-w-md space-y-4">
        {agents.map((agent) => {
          const status = agentStatus?.[agent.key]?.status || "pending";
          const color =
            status === "completed"
              ? "text-green-400"
              : status === "failed"
              ? "text-red-400"
              : status === "processing"
              ? "text-yellow-400"
              : "text-zinc-500";

          return (
            <motion.div
              key={agent.key}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center justify-between p-3 bg-zinc-900/30 rounded-lg border border-zinc-800/30"
            >
              <div className="flex items-center gap-2">
                <span className="text-2xl">{agent.icon}</span>
                <span className="text-zinc-200">{agent.label}</span>
              </div>
              <span className={`text-sm font-medium ${color}`}>{status}</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

const ItineraryView = ({ data, formData }) => {
  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      <h2 className="text-3xl font-light text-zinc-100 mb-4">
        Your AI Travel Plan
      </h2>

      <div className="bg-zinc-900/40 p-6 rounded-xl border border-zinc-800/50 space-y-4">
        <p className="text-zinc-300">
          <strong>From:</strong> {formData?.origin || "Unknown"}
        </p>
        <p className="text-zinc-300">
          <strong>To:</strong> {formData?.destination || "Unknown"}
        </p>
        <p className="text-zinc-300">
          <strong>Dates:</strong>{" "}
          {formData?.travel_dates?.join(", ") || "Unknown"}
        </p>
      </div>

      {data.weather_summary && (
        <div className="bg-zinc-900/40 p-6 rounded-xl border border-zinc-800/50">
          <h3 className="text-xl font-semibold text-zinc-100 mb-3">Weather</h3>
          <p className="text-zinc-300">{data.weather_summary}</p>
        </div>
      )}

      {data.itinerary_data && data.itinerary_data.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-2xl font-semibold text-zinc-100">Itinerary</h3>
          {data.itinerary_data.map((day, index) => (
            <div
              key={index}
              className="bg-zinc-900/40 p-4 rounded-xl border border-zinc-800/50"
            >
              <h4 className="text-xl font-semibold text-zinc-100 mb-2">
                Day {day.day}
              </h4>
              <p className="text-sm text-zinc-400 mb-3">{day.date}</p>
              <ul className="list-disc list-inside text-zinc-300 space-y-1">
                {day.activities?.map((act, idx) => (
                  <li key={idx}>{act}</li>
                ))}
              </ul>
              {day.notes && (
                <p className="mt-3 text-sm text-zinc-400 italic">{day.notes}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {data.events_data && data.events_data.length > 0 && (
        <div className="bg-zinc-900/40 p-6 rounded-xl border border-zinc-800/50">
          <h3 className="text-xl font-semibold text-zinc-100 mb-3">Events</h3>
          <div className="space-y-3">
            {data.events_data.slice(0, 5).map((event, idx) => (
              <div key={idx} className="border-l-2 border-amber-500 pl-3">
                <p className="font-medium text-zinc-200">{event.name}</p>
                <p className="text-sm text-zinc-400">
                  {event.date} at {event.time}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.budget_data && (
        <div className="bg-zinc-900/40 p-6 rounded-xl border border-zinc-800/50">
          <h3 className="text-xl font-semibold text-zinc-100 mb-3">Budget</h3>
          <div className="space-y-2 text-zinc-300">
            <p>Transportation: ${data.budget_data.transportation}</p>
            <p>Accommodation: ${data.budget_data.accommodation}</p>
            <p>Food: ${data.budget_data.food}</p>
            <p>Activities: ${data.budget_data.activities}</p>
            <p className="font-bold text-lg mt-3">
              Total: ${data.budget_data.total}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

// Generate a temporary session ID
const generateTempSessionId = () => {
  return `temp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const Page = () => {
  const [currentTitleIndex, setCurrentTitleIndex] = useState(0);
  const [isPlanning, setIsPlanning] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [planData, setPlanData] = useState({
    agent_status: {},
    weather_data: null,
    weather_summary: null,
    events_data: null,
    route_data: null,
    budget_data: null,
    itinerary_data: null,
    final_itinerary: null,
    completed_agents: 0,
    failed_agents: 0,
  });
  const [formData, setFormData] = useState(null);
  const [eventSource, setEventSource] = useState(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTitleIndex((prev) => (prev + 1) % titles.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  const handlePlanSubmit = async (payload) => {
    setFormData(payload);
    setIsPlanning(true);

    // CRITICAL: Generate session ID first
    const tempSessionId = generateTempSessionId();
    setSessionId(tempSessionId);

    // CRITICAL: Connect to SSE FIRST, before starting the workflow
    console.log("Connecting to SSE for session:", tempSessionId);
    const es = new EventSource(
      `http://localhost:8000/api/v1/stream/${tempSessionId}`
    );
    setEventSource(es);

    es.onopen = () => {
      console.log("SSE connection opened");
    };

    es.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        console.log("Received update:", update);

        if (update.type === "connected") {
          console.log("SSE connected, starting workflow...");
          // NOW start the workflow after SSE is connected
          startWorkflow(payload, tempSessionId);
          return;
        }

        if (update.type === "done" || update.type === "workflow_complete") {
          console.log("Workflow complete");
          es.close();
          return;
        }

        if (update.agent && update.data) {
          setPlanData((prev) => {
            const updated = { ...prev };

            if (update.data.weather_summary) {
              updated.weather_summary = update.data.weather_summary;
            }
            if (update.data.weather_data) {
              updated.weather_data = update.data.weather_data;
            }
            if (update.data.events_data) {
              updated.events_data = update.data.events_data;
            }
            if (update.data.route_data) {
              updated.route_data = update.data.route_data;
            }
            if (update.data.budget_data) {
              updated.budget_data = update.data.budget_data;
            }
            if (update.data.itinerary_data) {
              updated.itinerary_data = update.data.itinerary_data;
            }
            if (update.data.final_itinerary) {
              updated.final_itinerary = update.data.final_itinerary;
            }

            updated.agent_status = {
              ...prev.agent_status,
              [update.agent]: { status: "completed" },
            };

            updated.completed_agents = Object.values(
              updated.agent_status
            ).filter((s) => s.status === "completed").length;

            return updated;
          });
        }
      } catch (error) {
        console.error("Error parsing SSE message:", error);
      }
    };

    es.onerror = (err) => {
      console.error("SSE error:", err);
      es.close();
      alert("Connection lost. Please try again.");
      setIsPlanning(false);
    };
  };

  const startWorkflow = async (payload, sessionId) => {
    try {
      console.log("Starting workflow with session:", sessionId);
      const response = await fetch("http://localhost:8000/api/v1/plan-trip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...payload,
          session_id: sessionId, // Pass the temp session ID
        }),
      });

      if (!response.ok) throw new Error("Failed to generate plan");
      const result = await response.json();
      console.log("Workflow started:", result);
    } catch (error) {
      console.error("Error generating plan:", error);
      alert("Failed to generate travel plan. Please try again.");
      setIsPlanning(false);
    }
  };

  const handleNewPlan = () => {
    if (eventSource) {
      eventSource.close();
    }
    setIsPlanning(false);
    setSessionId(null);
    setPlanData({
      agent_status: {},
      weather_data: null,
      weather_summary: null,
      events_data: null,
      route_data: null,
      budget_data: null,
      itinerary_data: null,
      final_itinerary: null,
      completed_agents: 0,
      failed_agents: 0,
    });
    setFormData(null);
  };

  // Show results as soon as ANY data arrives
  const hasResults =
    planData.weather_summary ||
    planData.events_data ||
    planData.route_data ||
    planData.budget_data ||
    (planData.itinerary_data && planData.itinerary_data.length > 0);

  return (
    <div className="min-h-screen w-screen overflow-x-hidden bg-black relative">
      <HyperspeedBackground />
      <div className="bg-black/60 inset-0 absolute" />

      <div className="relative z-10">
        <AnimatePresence mode="wait">
          {!isPlanning ? (
            <motion.div
              key="landing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="min-h-screen flex flex-col items-center justify-center px-4 py-12"
            >
              <div className="mb-12 text-center">
                <AnimatePresence mode="wait">
                  <motion.h1
                    key={currentTitleIndex}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.5 }}
                    className="text-5xl font-light bg-gradient-to-r from-white via-zinc-300 to-zinc-700 bg-clip-text text-transparent mb-4"
                  >
                    {titles[currentTitleIndex]}
                  </motion.h1>
                </AnimatePresence>
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="text-zinc-400 text-lg"
                >
                  Fill in your travel details and let AI craft the perfect
                  itinerary
                </motion.p>
              </div>
              <TravelPlannerForm onSubmit={handlePlanSubmit} />
            </motion.div>
          ) : !hasResults ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <LoadingState agentStatus={planData.agent_status} />
            </motion.div>
          ) : (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="min-h-screen"
            >
              <div className="sticky top-0 z-20 backdrop-blur-xl bg-black/80 border-b border-zinc-800 px-4 py-4">
                <div className="max-w-6xl mx-auto flex justify-between items-center">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleNewPlan}
                    className="px-4 py-2 bg-zinc-800/50 hover:bg-zinc-700/50 border border-zinc-700 rounded-lg text-zinc-300 transition-all"
                  >
                    ← New Plan
                  </motion.button>
                  <div className="text-zinc-400 text-sm">
                    {planData.completed_agents} agents completed
                  </div>
                </div>
              </div>
              <div className="pt-8">
                <ItineraryView data={planData} formData={formData} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Page;
