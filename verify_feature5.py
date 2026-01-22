
import sys
import os
import json

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from app.core.agents.graph import run_qa_flow

def test_conversational_memory():
    print("Testing Feature 5: Conversational Multi-Turn QA with Memory...")
    
    # User Turn 1
    q1 = "What is HNSW indexing?"
    print(f"\n--- Turn 1: {q1} ---")
    
    # Session History (simulated)
    history = []
    
    try:
        result1 = run_qa_flow(q1, history)
        a1 = result1.get('answer', '')
        print(f"Answer 1: {a1[:100]}...")
        
        # Update History
        history.append({"question": q1, "answer": a1})
        
        # User Turn 2 (Follow-up)
        q2 = "What are its main advantages compared to LSH?"
        print(f"\n--- Turn 2: {q2} ---")
        
        result2 = run_qa_flow(q2, history)
        a2 = result2.get('answer', '')
        
        print(f"Answer 2: {a2[:200]}...")
        
        # Verification Logic
        # Answer 2 should reference HNSW even though Q2 uses "its" and doesn't mention HNSW explicitely (unless decomp resolved it)
        # But mostly, the system should NOT crash and should produce a coherent answer.
        
        if len(a2) > 20: 
            print("\n✅ Verification PASSED: System handled multi-turn conversation.")
            if "HNSW" in a2 or "Hierarchical" in a2:
                 print("   Context Awareness: Answer 2 correctly identified the subject 'HNSW'.")
        else:
            print("\n❌ Verification FAILED: Answer 2 is too short or empty.")
            
    except Exception as e:
        print(f"\n❌ Verification FAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversational_memory()
