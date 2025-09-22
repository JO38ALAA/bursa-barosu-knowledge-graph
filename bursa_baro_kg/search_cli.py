#!/usr/bin/env python3
"""
Bursa Barosu Bilgi Grafı - İnteraktif Arama CLI
Komut satırından semantik arama yapabileceğiniz arayüz
"""
import sys
import os
from search.engine import SemanticSearchEngine
from colorama import Fore, Style, init

# Colorama'yı başlat
init(autoreset=True)

def print_header():
    """Başlık yazdır"""
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🏛️  BURSA BAROSU BİLGİ GRAFI ARAMA SİSTEMİ  🏛️")
    print(f"{Fore.CYAN}{'='*60}")
    print()

def print_statistics(stats):
    """İstatistikleri yazdır"""
    print(f"{Fore.YELLOW}📊 Graf İstatistikleri:")
    for node_type, count in stats.get('nodes', {}).items():
        print(f"{Fore.WHITE}   • {node_type}: {Fore.GREEN}{count}")
    print(f"{Fore.WHITE}   • Toplam İlişki: {Fore.GREEN}{stats.get('total_relationships', 0)}")
    print()

def print_entity_results(entities):
    """Varlık sonuçlarını yazdır"""
    if not entities:
        print(f"{Fore.RED}❌ Sonuç bulunamadı")
        return
    
    print(f"{Fore.GREEN}✅ {len(entities)} varlık bulundu:")
    for i, entity in enumerate(entities, 1):
        print(f"{Fore.WHITE}   {i}. {Fore.CYAN}{entity['name']} {Fore.YELLOW}({entity['type']}) {Fore.MAGENTA}- {entity['mention_count']} kez geçiyor")

def print_relationship_results(relationships):
    """İlişki sonuçlarını yazdır"""
    if not relationships:
        print(f"{Fore.RED}❌ İlişki bulunamadı")
        return
    
    print(f"{Fore.GREEN}✅ {len(relationships)} ilişki bulundu:")
    for i, rel in enumerate(relationships, 1):
        print(f"{Fore.WHITE}   {i}. {Fore.CYAN}{rel['entity1']} {Fore.YELLOW}({rel['entity1_type']}) {Fore.WHITE}--[{Fore.RED}{rel['relation']}{Fore.WHITE}]--> {Fore.CYAN}{rel['entity2']} {Fore.YELLOW}({rel['entity2_type']})")

def print_document_results(documents):
    """Doküman sonuçlarını yazdır"""
    if not documents:
        print(f"{Fore.RED}❌ Doküman bulunamadı")
        return
    
    print(f"{Fore.GREEN}✅ {len(documents)} doküman bulundu:")
    for i, doc in enumerate(documents, 1):
        print(f"{Fore.WHITE}   {i}. {Fore.CYAN}{doc['title']}")
        print(f"{Fore.WHITE}      📄 {doc['url']}")
        print(f"{Fore.WHITE}      📏 {doc['content_length']} karakter")

def print_entity_context(context):
    """Varlık bağlamını yazdır"""
    if 'error' in context:
        print(f"{Fore.RED}❌ {context['error']}")
        return
    
    entity = context['entity']
    print(f"{Fore.GREEN}✅ Varlık Bilgisi:")
    print(f"{Fore.WHITE}   📋 Ad: {Fore.CYAN}{entity['name']}")
    print(f"{Fore.WHITE}   🏷️  Tür: {Fore.YELLOW}{entity['type']}")
    print(f"{Fore.WHITE}   📊 Geçme Sayısı: {Fore.MAGENTA}{entity['mention_count']}")
    
    if context['relationships']:
        print(f"\n{Fore.GREEN}🔗 İlişkiler:")
        for i, rel in enumerate(context['relationships'][:5], 1):
            print(f"{Fore.WHITE}   {i}. {Fore.CYAN}{rel['connected_entity']} {Fore.YELLOW}({rel['connected_entity_type']}) {Fore.WHITE}[{Fore.RED}{rel['relation_type']}{Fore.WHITE}]")
    
    if context['documents']:
        print(f"\n{Fore.GREEN}📄 İlgili Dokümanlar:")
        for i, doc in enumerate(context['documents'][:3], 1):
            print(f"{Fore.WHITE}   {i}. {Fore.CYAN}{doc['title']}")
            print(f"{Fore.WHITE}      🔗 {doc['url']}")

def print_help():
    """Yardım mesajını yazdır"""
    print(f"{Fore.YELLOW}📖 Kullanım Örnekleri:")
    print(f"{Fore.WHITE}   • {Fore.CYAN}Bursa{Fore.WHITE} - Varlık arama")
    print(f"{Fore.WHITE}   • {Fore.CYAN}Bursa Barosu kimdir{Fore.WHITE} - Varlık detayları")
    print(f"{Fore.WHITE}   • {Fore.CYAN}Bursa ile İstanbul arasındaki ilişki{Fore.WHITE} - İlişki arama")
    print(f"{Fore.WHITE}   • {Fore.CYAN}avukat dokümanları{Fore.WHITE} - Doküman arama")
    print(f"{Fore.WHITE}   • {Fore.CYAN}stats{Fore.WHITE} - İstatistikleri göster")
    print(f"{Fore.WHITE}   • {Fore.CYAN}help{Fore.WHITE} - Bu yardım mesajı")
    print(f"{Fore.WHITE}   • {Fore.CYAN}exit{Fore.WHITE} - Çıkış")
    print()

def main():
    """Ana fonksiyon"""
    try:
        # Arama motorunu başlat
        print(f"{Fore.YELLOW}🔄 Arama motoru başlatılıyor...")
        search_engine = SemanticSearchEngine()
        
        print_header()
        
        # İstatistikleri göster
        stats = search_engine.get_statistics()
        print_statistics(stats)
        
        print(f"{Fore.GREEN}✅ Arama motoru hazır! Sorgunuzu yazın (help: yardım, exit: çıkış)")
        print()
        
        while True:
            try:
                # Kullanıcı girdisi al
                query = input(f"{Fore.BLUE}🔍 Arama: {Fore.WHITE}").strip()
                
                if not query:
                    continue
                
                # Özel komutları kontrol et
                if query.lower() in ['exit', 'quit', 'çıkış']:
                    print(f"{Fore.YELLOW}👋 Görüşmek üzere!")
                    break
                
                elif query.lower() in ['help', 'yardım']:
                    print_help()
                    continue
                
                elif query.lower() in ['stats', 'istatistik']:
                    stats = search_engine.get_statistics()
                    print_statistics(stats)
                    continue
                
                # Arama yap
                print(f"{Fore.YELLOW}🔄 Aranıyor...")
                results = search_engine.advanced_search(query)
                
                print(f"\n{Fore.MAGENTA}📋 Arama Tipi: {results['search_type']}")
                print(f"{Fore.MAGENTA}🎯 Sorgu: {results['query']}")
                print()
                
                # Sonuçları göster
                if results['search_type'] == 'entity':
                    print_entity_results(results['results'])
                
                elif results['search_type'] == 'relationship':
                    print_relationship_results(results['results'])
                
                elif results['search_type'] == 'document':
                    print_document_results(results['results'])
                
                elif results['search_type'] == 'entity_context':
                    print_entity_context(results['results'])
                
                print(f"\n{Fore.CYAN}{'-'*60}")
                print()
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}👋 Görüşmek üzere!")
                break
            
            except Exception as e:
                print(f"{Fore.RED}❌ Hata: {e}")
                print()
    
    except Exception as e:
        print(f"{Fore.RED}❌ Arama motoru başlatılamadı: {e}")
        print(f"{Fore.YELLOW}💡 Neo4j'nin çalıştığından emin olun: docker ps")
        sys.exit(1)
    
    finally:
        if 'search_engine' in locals():
            search_engine.close()

if __name__ == "__main__":
    main()
