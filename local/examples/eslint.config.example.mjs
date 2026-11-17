// Example only. Shows bans whose error messages point at the root-cause fix,
// following the talk's Dune examples. Adapt the paths and alternatives to your codebase.
export default [
  {
    files: ["src/renderer/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-globals": ["error",
        { name: "setTimeout", message: "Timers in the renderer usually hide an ownership or lifecycle mismatch. Subscribe to the store or event that owns this state instead." },
        { name: "requestAnimationFrame", message: "Use the animation/scheduling API from src/renderer/platform instead of raw frame callbacks." },
        { name: "requestIdleCallback", message: "Use the scheduling API from src/renderer/platform instead of idle callbacks." },
      ],
      "no-restricted-properties": ["error",
        { object: "window", property: "setTimeout", message: "See the setTimeout rule: fix the ownership instead of deferring." },
      ],
      "no-restricted-syntax": ["error",
        {
          selector: "CallExpression[callee.name='useEffect']",
          message: "useEffect is not allowed in product code. Use the data hooks in src/renderer/framework (useQuery, useSubscription) or derive the value during render.",
        },
      ],
    },
  },
];
