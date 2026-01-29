
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

def check_step_1_schema():
    print("Checking Step 1: Schema...", end=" ")
    try:
        from src.schemas.state_schema import StateFieldType
        if hasattr(StateFieldType, "OPTIONAL_FLOAT") and hasattr(StateFieldType, "OPTIONAL_DICT"):
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL (Missing Enum members)")
            return False
    except ImportError as e:
        print(f"❌ FAIL (Import Error: {e})")
        return False

def check_step_2_vectorstore():
    print("Checking Step 2: VectorStore Template...", end=" ")
    try:
        content = Path("src/templates/rag_vectorstore.py.j2").read_text(encoding="utf-8")
        if "get_config_hash" in content and "hashlib.md5" in content and "shutil.rmtree" in content:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL (Missing hash logic)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Read Error: {e})")
        return False

def check_step_3_loader():
    print("Checking Step 3: DocumentLoader Template...", end=" ")
    try:
        content = Path("src/templates/rag_document_loader.py.j2").read_text(encoding="utf-8")
        # Check if we always load documents (no condition on vectorstore count before loading)
        if "documents = load_documents" in content and "if existing_count > 0" not in content:
            # We removed the 'if existing_count > 0' check, so it shouldn't be there or should be modified
            # Actually we replaced it. Let's check for the positive case:
            if "Smart update" in content or "Checking vector store status" in content: 
                 # My specific strings might vary, let's check for the logic structure
                 pass
            
        # The key is that we removed the 'checking existing count BEFORE loading'
        # and checking it AFTER loading.
        
        if "if vectorstore._collection.count() == 0" in content:
             print("✅ PASS (Found conditional add)")
             return True
        else:
             # It might be creating FAISS differently
            if "if vectorstore is None" in content: # FAISS check
                print("✅ PASS (Found FAISS check)")
                return True
            print("❌ FAIL (Could not find conditional logic)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Read Error: {e})")
        return False

def check_step_4_optimizer():
    print("Checking Step 4: Optimizer Prompt...", end=" ")
    try:
        content = Path("src/core/rag_optimizer.py").read_text(encoding="utf-8")
        if "Emergency Protocol" in content and "Contextual Recall" in content:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL (Missing Emergency Protocol)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Read Error: {e})")
        return False


def check_compiler_deps():
    print("Checking Step 5: Compiler Dependencies...", end=" ")
    try:
        content = Path("src/core/compiler.py").read_text(encoding="utf-8")
        if 'requirements.append("rank-bm25>=0.2.2")' in content and 'requirements.append("flashrank>=0.2.0")' in content:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL (Diff not found)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Error: {e})")
        return False

def check_vectorstore_runtime_hash():
    print("Checking Step 6: VectorStore Runtime Hash...", end=" ")
    try:
        content = Path("src/templates/rag_vectorstore.py.j2").read_text(encoding="utf-8")
        if "CONFIG_LOADER.load_rag_config()" in content:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL (Diff not found)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Error: {e})")
        return False

def check_optimizer_constraints():
    print("Checking Step 7: Optimizer Constraints...", end=" ")
    try:
        content = Path("src/core/rag_optimizer.py").read_text(encoding="utf-8")
        if "最佳实践约束 (Best Practices)" in content and "Chunk Size" in content:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL (Diff not found)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Error: {e})")
        return False

def check_reranker_logic():
    print("Checking Step 8: Reranker Top-N...", end=" ")
    try:
        content = Path("src/templates/rag_retriever.py.j2").read_text(encoding="utf-8")
        if "final_top_n = min(k, 10)" in content:
            print("✅ PASS")
            return True
        else:
            print("❌ FAIL (Diff not found)")
            return False
    except Exception as e:
        print(f"❌ FAIL (Error: {e})")
        return False

if __name__ == "__main__":
    print("Running Static Verification for Agent Zero v7.2 Repairs...\n")
    results = [
        check_step_1_schema(),
        check_step_2_vectorstore(),
        check_step_3_loader(),
        check_step_4_optimizer(),
        check_compiler_deps(),
        check_vectorstore_runtime_hash(),
        check_optimizer_constraints(),
        check_reranker_logic()
    ]
    
    if all(results):
        print("\n✨ All repairs passed static verification!")
        sys.exit(0)
    else:
        print("\n⚠️ Some repairs failed verification.")
        sys.exit(1)
