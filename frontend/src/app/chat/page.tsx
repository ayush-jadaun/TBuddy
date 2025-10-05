'use client'
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

    // Filter out empty dates and validate
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

      {/* Required Fields */}
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

        {/* Travel Dates */}
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

        {/* Travelers Count and Budget */}
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

        {/* Preferences Section */}
        <div className="pt-6 border-t border-zinc-800">
          <h3 className="text-xl font-light text-zinc-100 mb-4">
            Preferences (Optional)
          </h3>

          {/* Interests */}
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

          {/* Pace and Group Type */}
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

          {/* Dietary Restrictions */}
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

          {/* Accessibility Needs */}
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

        {/* Submit Button */}
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

const LoadingState = () => {
  const stages = [
    { text: "Ringmaster is thinking", icon: "🎪" },
    { text: "Analyzing your preferences", icon: "🔍" },
    { text: "Checking weather conditions", icon: "🌤️" },
    { text: "Finding the best routes", icon: "🗺️" },
    { text: "Calculating your budget", icon: "💰" },
    { text: "Crafting your perfect itinerary", icon: "✨" },
  ];

  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStage((prev) => (prev + 1) % stages.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center space-y-8 min-h-screen">
      <motion.div
        className="relative"
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
      >
        <div className="w-20 h-20 border-4 border-red-900/30 border-t-red-500 rounded-full" />
      </motion.div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentStage}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="text-center"
        >
          <div className="text-4xl mb-3">{stages[currentStage].icon}</div>
          <div className="text-xl text-zinc-300 font-light">
            {stages[currentStage].text}
          </div>
        </motion.div>
      </AnimatePresence>

      <div className="flex gap-2">
        {stages.map((_, i) => (
          <motion.div
            key={i}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              i === currentStage ? "w-8 bg-red-500" : "w-1.5 bg-zinc-700"
            }`}
          />
        ))}
      </div>
    </div>
  );
};

const ItineraryView = ({ data, formData }) => {
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: data.budget?.currency || "INR",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getWeatherIcon = (description) => {
    if (!description) return "🌤️";
    if (description.includes("rain")) return "🌧️";
    if (description.includes("cloud")) return "☁️";
    if (description.includes("sun")) return "☀️";
    return "🌤️";
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full max-w-6xl mx-auto px-4 pb-20"
    >
      {/* Trip Summary */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 p-6 bg-zinc-900/50 backdrop-blur-md border border-zinc-800 rounded-2xl"
      >
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-red-500 flex items-center justify-center text-white font-bold text-lg">
            📍
          </div>
          <div className="flex-1">
            <h3 className="text-2xl font-light text-zinc-100 mb-2">
              {formData.origin} → {formData.destination}
            </h3>
            <div className="flex flex-wrap gap-4 text-sm text-zinc-400">
              <span>
                👥 {formData.travelers_count} traveler
                {formData.travelers_count > 1 ? "s" : ""}
              </span>
              <span>📅 {formData.travel_dates.length} days</span>
              {formData.budget_range && <span>💵 {formData.budget_range}</span>}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Budget Overview */}
      {data.budget && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8 p-6 bg-gradient-to-br from-red-900/20 to-amber-900/20 backdrop-blur-md border border-red-800/30 rounded-2xl"
        >
          <h3 className="text-xl font-light text-zinc-100 mb-4 flex items-center gap-2">
            💰 Budget Breakdown
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-400">
                {formatCurrency(data.budget.total)}
              </div>
              <div className="text-sm text-zinc-400">Total</div>
            </div>
            <div className="text-center">
              <div className="text-lg text-zinc-300">
                {formatCurrency(data.budget.transportation)}
              </div>
              <div className="text-sm text-zinc-400">Transport</div>
            </div>
            <div className="text-center">
              <div className="text-lg text-zinc-300">
                {formatCurrency(data.budget.accommodation)}
              </div>
              <div className="text-sm text-zinc-400">Stay</div>
            </div>
            <div className="text-center">
              <div className="text-lg text-zinc-300">
                {formatCurrency(data.budget.food)}
              </div>
              <div className="text-sm text-zinc-400">Food</div>
            </div>
            <div className="text-center">
              <div className="text-lg text-zinc-300">
                {formatCurrency(data.budget.activities)}
              </div>
              <div className="text-sm text-zinc-400">Activities</div>
            </div>
          </div>
        </motion.div>
      )}
      {/* Events */}
      {data.events && data.events.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="mb-8 p-6 bg-black/40 backdrop-blur-md border border-zinc-800/50 rounded-2xl"
        >
          <h3 className="text-xl font-light text-zinc-100 mb-4 flex items-center gap-2">
            🎉 Local Events
          </h3>
          <div className="space-y-4">
            {data.events.map((event, index) => (
              <div
                key={index}
                className="p-4 bg-zinc-900/30 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-lg text-zinc-200 font-medium">
                    {event.name}
                  </h4>
                  <span className="text-xs px-2 py-1 bg-amber-900/30 text-amber-400 rounded-full">
                    {event.category}
                  </span>
                </div>
                <div className="space-y-1 text-sm text-zinc-400">
                  <div className="flex items-center gap-2">
                    <span>📅</span>
                    <span>
                      {event.date} at {event.time}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>📍</span>
                    <span>{event.venue}</span>
                  </div>
                  {event.description && (
                    <p className="text-zinc-500 mt-2">{event.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Route Information */}
      {data.route && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-8 p-6 bg-black/40 backdrop-blur-md border border-zinc-800/50 rounded-2xl"
        >
          <h3 className="text-xl font-light text-zinc-100 mb-4 flex items-center gap-2">
            🗺️ Route Details
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
            <div>
              <div className="text-sm text-zinc-400">Distance</div>
              <div className="text-lg text-zinc-100">{data.route.distance}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-400">Duration</div>
              <div className="text-lg text-zinc-100">{data.route.duration}</div>
            </div>
            <div>
              <div className="text-sm text-zinc-400">Mode</div>
              <div className="text-lg text-zinc-100 capitalize">
                {data.route.transport_mode}
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Daily Itinerary */}
      {data.itinerary?.map((day, index) => (
        <motion.div
          key={day.day}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 + index * 0.1 }}
          className="mb-6 p-6 bg-black/40 backdrop-blur-md border border-zinc-800/50 rounded-2xl hover:border-zinc-700/50 transition-all"
        >
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-2xl font-light text-zinc-100 mb-1">
                Day {day.day}
              </h3>
              <p className="text-zinc-400">{day.date}</p>
            </div>
            <div className="text-right">
              <div className="text-lg text-amber-400 font-semibold">
                {formatCurrency(day.estimated_cost)}
              </div>
              {data.weather?.[index] && (
                <div className="text-sm text-zinc-400 flex items-center gap-2 mt-1">
                  <span>{getWeatherIcon(data.weather[index].description)}</span>
                  <span>
                    {Math.round(data.weather[index].temperature_max)}°C
                  </span>
                </div>
              )}
            </div>
          </div>

          {day.notes && (
            <div className="mb-4 p-3 bg-amber-900/10 border border-amber-800/30 rounded-lg">
              <p className="text-sm text-amber-200/80 flex items-start gap-2">
                <span className="text-amber-500">⚠️</span>
                {day.notes}
              </p>
            </div>
          )}

          <div className="space-y-3">
            {day.activities?.map((activity, actIndex) => (
              <motion.div
                key={actIndex}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 + actIndex * 0.05 }}
                className="flex gap-3 items-start group"
              >
                <div className="w-2 h-2 mt-2 rounded-full bg-red-800 group-hover:bg-red-500 transition-colors flex-shrink-0" />
                <p className="text-zinc-300 group-hover:text-zinc-100 transition-colors">
                  {activity}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      ))}

      {/* Processing Info */}
      {data.agent_status && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 p-6 bg-zinc-900/30 backdrop-blur-md border border-zinc-800/30 rounded-2xl"
        >
          <h3 className="text-lg font-light text-zinc-100 mb-4">
            Processing Details
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
            {Object.entries(data.agent_status).map(([agent, status]) => (
              <div key={agent} className="p-3 bg-black/30 rounded-lg">
                <div className="text-sm text-zinc-400 capitalize mb-1">
                  {agent}
                </div>
                <div
                  className={`text-xs font-medium ${
                    status.status === "completed"
                      ? "text-green-400"
                      : status.status === "failed"
                      ? "text-red-400"
                      : "text-yellow-400"
                  }`}
                >
                  {status.status}
                </div>
                {status.duration_ms && (
                  <div className="text-xs text-zinc-500 mt-1">
                    {(status.duration_ms / 1000).toFixed(1)}s
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

const Page = () => {
  const [currentTitleIndex, setCurrentTitleIndex] = useState(0);
  const [isPlanning, setIsPlanning] = useState(false);
  const [planData, setPlanData] = useState(null);
  const [formData, setFormData] = useState(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTitleIndex((prev) => (prev + 1) % titles.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handlePlanSubmit = async (payload) => {
    setFormData(payload);
    setIsPlanning(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/plan-trip", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Failed to generate plan");
      }

      const result = await response.json();
      setPlanData(result.data);
    } catch (error) {
      console.error("Error generating plan:", error);
      alert("Failed to generate travel plan. Please try again.");
      setIsPlanning(false);
    }
  };

  const handleNewPlan = () => {
    setIsPlanning(false);
    setPlanData(null);
    setFormData(null);
  };

  return (
    <div className="min-h-screen w-screen overflow-x-hidden bg-black relative">
      <HyperspeedBackground />
      <div className="bg-black/60 inset-0 absolute" />

      <div className="relative z-10">
        <AnimatePresence mode="wait">
          {!isPlanning && !planData ? (
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
            
          ) : !planData ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <LoadingState />
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
                    {planData.completed_agents} /{" "}
                    {planData.completed_agents + planData.failed_agents} agents
                    completed
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
