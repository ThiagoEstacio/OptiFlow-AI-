#!/usr/bin/env python3
"""
Test Tag Labels API
Validates the new tag labels system
"""
import requests
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_list_labels():
    """Test listing all labels"""
    print_section("1. Listar Todos os Labels")
    
    response = requests.get(f"{BACKEND_URL}/api/v1/tag-labels/", timeout=5)
    
    if response.status_code == 200:
        labels = response.json()
        print(f"✅ {len(labels)} labels encontrados\n")
        
        # Mostrar primeiros 5
        for i, label in enumerate(labels[:5], 1):
            print(f"{i}. {label['display_name']}")
            print(f"   Tag ID: {label['tag_id']}")
            print(f"   Equipamento: {label.get('equipment_name', 'N/A')}")
            print(f"   Área: {label.get('area_name', 'N/A')}")
            print(f"   Favorito: {'⭐' if label.get('is_favorite') else '❌'}")
            print()
        
        if len(labels) > 5:
            print(f"   ... e mais {len(labels) - 5} labels")
        
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return False

def test_search_by_area():
    """Test searching by area"""
    print_section("2. Buscar por Área (Armazém 01)")
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/tag-labels/",
        params={"area_name": "Armazém 01"},
        timeout=5
    )
    
    if response.status_code == 200:
        labels = response.json()
        print(f"✅ {len(labels)} labels encontrados no Armazém 01\n")
        
        # Agrupar por equipamento
        equipments = {}
        for label in labels:
            eq = label.get('equipment_name', 'Sem Equipamento')
            if eq not in equipments:
                equipments[eq] = []
            equipments[eq].append(label['display_name'])
        
        for eq, names in equipments.items():
            print(f"📦 {eq}:")
            for name in names:
                print(f"   • {name}")
            print()
        
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False

def test_get_favorites():
    """Test getting favorites"""
    print_section("3. Labels Favoritos ⭐")
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/tag-labels/",
        params={"is_favorite": True},
        timeout=5
    )
    
    if response.status_code == 200:
        labels = response.json()
        print(f"✅ {len(labels)} labels favoritos\n")
        
        for i, label in enumerate(labels, 1):
            print(f"{i}. ⭐ {label['display_name']}")
            print(f"   {label.get('area_name', 'N/A')} > {label.get('equipment_name', 'N/A')}")
            print()
        
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False

def test_get_stats():
    """Test statistics endpoint"""
    print_section("4. Estatísticas dos Labels")
    
    response = requests.get(f"{BACKEND_URL}/api/v1/tag-labels/stats/overview", timeout=5)
    
    if response.status_code == 200:
        stats = response.json()
        
        print(f"📊 Total de Tags: {stats['total_tags']}")
        print(f"🏷️  Tags com Label: {stats['labeled_tags']} ({stats['labeled_tags']/stats['total_tags']*100:.1f}%)")
        print(f"❌ Tags sem Label: {stats['unlabeled_tags']}")
        print(f"⭐ Favoritos: {stats['favorite_tags']}")
        print(f"📍 Áreas: {stats['areas_count']}")
        print(f"🔧 Equipamentos: {stats['equipments_count']}")
        print(f"⚙️  Sistemas: {stats['systems_count']}")
        
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        return False

def test_get_filters():
    """Test filter endpoints"""
    print_section("5. Filtros Disponíveis")
    
    # Areas
    response = requests.get(f"{BACKEND_URL}/api/v1/tag-labels/filters/areas", timeout=5)
    if response.status_code == 200:
        areas = response.json()
        print(f"📍 Áreas ({len(areas)}):")
        for area in areas:
            print(f"   • {area}")
    
    # Equipments
    response = requests.get(f"{BACKEND_URL}/api/v1/tag-labels/filters/equipments", timeout=5)
    if response.status_code == 200:
        equipments = response.json()
        print(f"\n🔧 Equipamentos ({len(equipments)}):")
        for eq in equipments[:10]:  # Limitar a 10
            print(f"   • {eq}")
        if len(equipments) > 10:
            print(f"   ... e mais {len(equipments) - 10}")
    
    # Systems
    response = requests.get(f"{BACKEND_URL}/api/v1/tag-labels/filters/systems", timeout=5)
    if response.status_code == 200:
        systems = response.json()
        print(f"\n⚙️  Sistemas ({len(systems)}):")
        for sys in systems:
            print(f"   • {sys}")
    
    return True

def test_tags_with_labels():
    """Test tags with labels endpoint"""
    print_section("6. Tags com Labels (Visão Combinada)")
    
    response = requests.get(
        f"{BACKEND_URL}/api/v1/tag-labels/tags/with-labels",
        params={"limit": 5, "include_unlabeled": False},
        timeout=5
    )
    
    if response.status_code == 200:
        tags = response.json()
        print(f"✅ {len(tags)} tags encontradas\n")
        
        for i, tag in enumerate(tags, 1):
            print(f"{i}. Nome Original: {tag['name']}")
            print(f"   Nome Amigável: {tag['effective_name']}")
            if tag.get('label'):
                print(f"   Equipamento: {tag['label'].get('equipment_name', 'N/A')}")
                print(f"   Área: {tag['label'].get('area_name', 'N/A')}")
            print(f"   Unidade: {tag.get('unit', 'N/A')}")
            print()
        
        return True
    else:
        print(f"❌ Erro: {response.status_code}")
        print(response.text)
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏷️  Tag Labels API - Teste de Validação")
    print("="*80)
    print(f"Backend: {BACKEND_URL}")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Listar Labels", test_list_labels),
        ("Buscar por Área", test_search_by_area),
        ("Labels Favoritos", test_get_favorites),
        ("Estatísticas", test_get_stats),
        ("Filtros", test_get_filters),
        ("Tags com Labels", test_tags_with_labels),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erro no teste '{test_name}': {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("📊 Resumo dos Testes")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*80}")
    print(f"Resultado: {passed}/{total} testes passaram ({passed/total*100:.0f}%)")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("🎉 Todos os testes passaram! Sistema de Tag Labels funcionando perfeitamente.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        return 1

if __name__ == "__main__":
    exit(main())
