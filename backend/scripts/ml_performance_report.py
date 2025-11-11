"""
📊 ML MODEL PERFORMANCE REPORT

Gera relatório comparativo dos modelos treinados
"""

import os
import json
import joblib
from datetime import datetime

MODEL_DIR = "/app/models"

def generate_report():
    print("\n" + "=" * 70)
    print("📊 ML MODEL PERFORMANCE REPORT")
    print("=" * 70)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check for existing models
    models = []
    
    # Baseline model
    baseline_path = f"{MODEL_DIR}/isolation_forest.joblib"
    if os.path.exists(baseline_path):
        stat = os.stat(baseline_path)
        models.append({
            'name': 'Isolation Forest (Baseline)',
            'file': 'isolation_forest.joblib',
            'size': stat.st_size / 1024,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Optimized model
    optimized_path = f"{MODEL_DIR}/isolation_forest_optimized.joblib"
    if os.path.exists(optimized_path):
        stat = os.stat(optimized_path)
        models.append({
            'name': 'Isolation Forest (Optimized)',
            'file': 'isolation_forest_optimized.joblib',
            'size': stat.st_size / 1024,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Production model
    production_path = f"{MODEL_DIR}/isolation_forest_production.joblib"
    if os.path.exists(production_path):
        stat = os.stat(production_path)
        models.append({
            'name': 'Isolation Forest (Production)',
            'file': 'isolation_forest_production.joblib',
            'size': stat.st_size / 1024,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    if not models:
        print("⚠️  No models found in /app/models/")
        return
    
    print("🤖 AVAILABLE MODELS:")
    print("-" * 70)
    for model in models:
        print(f"\n{model['name']}")
        print(f"   File: {model['file']}")
        print(f"   Size: {model['size']:.1f} KB")
        print(f"   Last Modified: {model['modified']}")
    
    # Load and display metrics
    print("\n\n📈 PERFORMANCE METRICS:")
    print("-" * 70)
    
    metrics_files = [
        ('metrics.json', 'Baseline Metrics'),
        ('metrics_optimized.json', 'Optimized Metrics'),
        ('metrics_production.json', 'Production Metrics'),
    ]
    
    all_metrics = {}
    
    for filename, label in metrics_files:
        path = f"{MODEL_DIR}/{filename}"
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                all_metrics[label] = data
                
                print(f"\n{label}:")
                
                # Find the main model metrics
                if 'isolation_forest' in data:
                    metrics = data['isolation_forest']
                elif 'model' in data:
                    metrics = data
                else:
                    metrics = data
                
                if isinstance(metrics, dict):
                    if 'f1_score' in metrics:
                        print(f"   F1-Score:  {metrics['f1_score']:.4f}")
                    if 'precision' in metrics:
                        print(f"   Precision: {metrics['precision']:.4f}")
                    if 'recall' in metrics:
                        print(f"   Recall:    {metrics['recall']:.4f}")
                    
                    # Show confusion matrix if available
                    if 'confusion_matrix' in metrics:
                        cm = metrics['confusion_matrix']
                        if isinstance(cm, list) and len(cm) == 2:
                            tn, fp = cm[0]
                            fn, tp = cm[1]
                            print(f"   Confusion Matrix:")
                            print(f"      TN={tn:,}  FP={fp:,}")
                            print(f"      FN={fn:,}  TP={tp:,}")
                
                # Show ensemble metrics if available
                if 'ensemble' in data:
                    ens = data['ensemble']
                    print(f"\n   Ensemble Model:")
                    if 'f1_score' in ens:
                        print(f"      F1-Score:  {ens['f1_score']:.4f}")
                    if 'precision' in ens:
                        print(f"      Precision: {ens['precision']:.4f}")
                    if 'recall' in ens:
                        print(f"      Recall:    {ens['recall']:.4f}")
    
    # Comparison
    if len(all_metrics) > 1:
        print("\n\n📊 COMPARATIVE ANALYSIS:")
        print("-" * 70)
        
        baseline_f1 = 0.1032  # Known baseline
        
        for label, data in all_metrics.items():
            if 'isolation_forest' in data:
                f1 = data['isolation_forest'].get('f1_score', 0)
            elif 'f1_score' in data:
                f1 = data['f1_score']
            else:
                continue
            
            improvement = (f1 / baseline_f1 - 1) * 100
            print(f"\n{label}:")
            print(f"   F1-Score: {f1:.4f}")
            print(f"   vs Baseline: {improvement:+.1f}%")
    
    # Recommendations
    print("\n\n💡 RECOMMENDATIONS:")
    print("-" * 70)
    
    best_f1 = 0
    best_model = None
    
    for label, data in all_metrics.items():
        if 'isolation_forest' in data:
            f1 = data['isolation_forest'].get('f1_score', 0)
        elif 'f1_score' in data:
            f1 = data['f1_score']
        else:
            continue
        
        if f1 > best_f1:
            best_f1 = f1
            best_model = label
    
    if best_model:
        print(f"\n✅ Best Model: {best_model} (F1={best_f1:.4f})")
    
    if best_f1 < 0.25:
        print("\n⚠️  F1-Score ainda baixo para produção (<0.25)")
        print("\n📋 Próximos passos recomendados:")
        print("   1. ✅ Feature Engineering - adicionar mais features derivadas")
        print("   2. ✅ Ensemble Methods - combinar múltiplos modelos")
        print("   3. 🔄 Hyperparameter Tuning - otimizar parâmetros")
        print("   4. 🔄 Data Augmentation - balancear classes")
        print("   5. 🔄 Deep Learning - LSTM/Autoencoder para sequências temporais")
    elif best_f1 < 0.5:
        print("\n⚡ F1-Score moderado (0.25-0.5) - Bom para validação")
        print("\n📋 Melhorias sugeridas:")
        print("   1. Fine-tune ensemble weights")
        print("   2. Add domain-specific rules")
        print("   3. Implement feedback loop")
    else:
        print("\n✨ F1-Score excelente (>0.5) - Pronto para produção!")
        print("\n📋 Próximos passos:")
        print("   1. Deploy to production API")
        print("   2. Set up monitoring and alerts")
        print("   3. Implement feedback mechanism")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    generate_report()
