from .base_agent import BaseAgent

class AnalysisAgent(BaseAgent):
    def run(self, prompt: str) -> str:
        qwen = self.tools.get("qwen_api")
        if not qwen:
            return "Error: AI tool not available."
        
        # Prepend context to frame the AI's persona
        context = "You are FinMind, an intelligent financial assistant. Answer the user's question concisely and helpfully regarding their finances or general queries."
        full_prompt = f"{context}\n\nUser Question: {prompt}\n\nAnswer:"
        
        try:
            try:
                print(f"[FinMind][Agent] query={str(prompt)[:200]}")
            except Exception:
                pass
            ans = qwen.call(full_prompt)
            try:
                print(f"[FinMind][Agent] answer={str(ans)[:200]}")
            except Exception:
                pass
            return ans
        except Exception as e:
            return f"Error processing request: {str(e)}"
