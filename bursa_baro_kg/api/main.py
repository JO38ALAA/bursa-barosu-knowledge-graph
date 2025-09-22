"""
Bursa Barosu Bilgi Grafı - FastAPI Web Servisi
REST API endpoints ile semantik arama servisi
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os

# Search engine'i import et
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from search.engine import SemanticSearchEngine
from scheduler.updater import get_updater

# FastAPI app oluştur
app = FastAPI(
    title="Bursa Barosu Semantik Arama API",
    description="""
    ## Bursa Barosu Bilgi Grafı ve Semantik Arama API'si
    
    Bu API, Bursa Barosu web sitesinden çıkarılan bilgileri kullanarak:
    
    * **🔍 Gelişmiş Semantik Arama** - Doğal dil ile akıllı arama
    * **👥 Varlık Keşfi** - Kişi, kurum, yer, tarih ve hukuki terim arama
    * **🔗 İlişki Analizi** - Varlıklar arası bağlantıları keşfetme
    * **📄 Doküman Arama** - İçerik tabanlı doküman bulma
    * **🕸️ Graf Görselleştirme** - İnteraktif bilgi grafı
    * **📊 İstatistikler** - Graf analiz verileri
    
    ### Kullanım Örnekleri:
    - `Bursa Barosu` - Varlık arama
    - `Bursa Barosu kimdir` - Varlık detayları
    - `avukat dokümanları` - Doküman arama
    - `Bursa ile İstanbul arasındaki ilişki` - İlişki arama
    
    ### Graf Görselleştirme:
    [🕸️ İnteraktif Graf](/graph) | [📊 İstatistikler](/stats)
    """,
    version="1.0.0",
    contact={
        "name": "Bursa Barosu Bilgi Grafı Projesi",
        "url": "https://bursabarosu.org.tr",
    },
    license_info={
        "name": "MIT License",
    },
)

# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global search engine instance
search_engine = None

# Pydantic modelleri
class SearchRequest(BaseModel):
    query: str
    entity_type: Optional[str] = None
    limit: Optional[int] = 10

class EntityResponse(BaseModel):
    name: str
    type: str
    mention_count: int

class RelationshipResponse(BaseModel):
    entity1: str
    entity1_type: str
    relation: str
    entity2: str
    entity2_type: str
    strength: int

class DocumentResponse(BaseModel):
    url: str
    title: str
    content_length: int

class SearchResponse(BaseModel):
    search_type: str
    query: str
    results: List[Dict]

class StatsResponse(BaseModel):
    nodes: Dict[str, int]
    total_nodes: int
    total_relationships: int

@app.on_event("startup")
async def startup_event():
    """Uygulama başlatılırken search engine'i başlat"""
    global search_engine
    try:
        search_engine = SemanticSearchEngine()
        print("✅ Search engine başlatıldı")
    except Exception as e:
        print(f"❌ Search engine başlatma hatası: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapatılırken kaynakları temizle"""
    global search_engine
    if search_engine:
        search_engine.close()
        print("✅ Search engine kapatıldı")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Ana sayfa - basit web arayüzü"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bursa Barosu Bilgi Grafı</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
            .search-box { margin: 20px 0; }
            input[type="text"] { width: 70%; padding: 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 16px; }
            button { padding: 12px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-left: 10px; }
            button:hover { background: #2980b9; }
            .results { margin-top: 30px; }
            .entity { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }
            .stats { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .examples { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .loading { color: #7f8c8d; font-style: italic; }
        </style>
    </head>
    <body>
        <div class="search-container">
            <h1>🔍 Bursa Barosu Semantik Arama</h1>
            <p>Bursa Barosu bilgi grafında akıllı arama yapın</p>
            <div style="text-align: center; margin-bottom: 20px;">
                <a href="/graph" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px;">🕸️ Bilgi Grafını Görüntüle</a>
                <a href="/stats" style="background: #17a2b8; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">📊 İstatistikler</a>
            </div>
            <div class="examples">
                <h3>📖 Örnek Aramalar:</h3>
                <ul>
                    <li><strong>Bursa</strong> - Varlık arama</li>
                    <li><strong>Bursa Barosu kimdir</strong> - Varlık detayları</li>
                    <li><strong>avukat dokümanları</strong> - Doküman arama</li>
                    <li><strong>Bursa ile İstanbul arasındaki ilişki</strong> - İlişki arama</li>
                </ul>
            </div>
            
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Arama sorgunuzu yazın..." onkeypress="handleKeyPress(event)">
                <button onclick="search()">🔍 Ara</button>
                <button onclick="getStats()">📊 İstatistik</button>
            </div>
            
            <div id="results" class="results"></div>
        </div>

        <script>
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    search();
                }
            }

            async function search() {
                const query = document.getElementById('searchInput').value.trim();
                if (!query) {
                    alert('Lütfen bir arama sorgusu girin');
                    return;
                }

                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="loading">🔄 Aranıyor...</div>';

                try {
                    const response = await fetch(`/search?query=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    displayResults(data);
                } catch (error) {
                    resultsDiv.innerHTML = `<div style="color: red;">❌ Hata: ${error.message}</div>`;
                }
            }

            async function getStats() {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="loading">📊 İstatistikler yükleniyor...</div>';

                try {
                    const response = await fetch('/stats');
                    const data = await response.json();
                    
                    let html = '<div class="stats"><h3>📊 Graf İstatistikleri</h3>';
                    for (const [nodeType, count] of Object.entries(data.nodes)) {
                        html += `<p><strong>${nodeType}:</strong> ${count}</p>`;
                    }
                    html += `<p><strong>Toplam İlişki:</strong> ${data.total_relationships}</p></div>`;
                    
                    resultsDiv.innerHTML = html;
                } catch (error) {
                    resultsDiv.innerHTML = `<div style="color: red;">❌ Hata: ${error.message}</div>`;
                }
            }

            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                let html = `<h3>🎯 Arama Sonuçları (${data.search_type})</h3>`;
                
                if (data.search_type === 'entity') {
                    if (data.results.length === 0) {
                        html += '<p>❌ Sonuç bulunamadı</p>';
                    } else {
                        data.results.forEach((entity, index) => {
                            html += `<div class="entity">
                                <strong>${index + 1}. ${entity.name}</strong> 
                                <span style="color: #7f8c8d;">(${entity.type})</span>
                                <br><small>📊 ${entity.mention_count} kez geçiyor</small>
                            </div>`;
                        });
                    }
                } else if (data.search_type === 'entity_context') {
                    const context = data.results;
                    if (context.error) {
                        html += `<p style="color: red;">❌ ${context.error}</p>`;
                    } else {
                        const entity = context.entity;
                        html += `<div class="entity">
                            <h4>📋 ${entity.name} (${entity.type})</h4>
                            <p>📊 ${entity.mention_count} kez geçiyor</p>
                        </div>`;
                        
                        if (context.relationships.length > 0) {
                            html += '<h4>🔗 İlişkiler:</h4>';
                            context.relationships.slice(0, 5).forEach((rel, index) => {
                                html += `<div class="entity">
                                    ${index + 1}. <strong>${rel.connected_entity}</strong> 
                                    <span style="color: #7f8c8d;">(${rel.connected_entity_type})</span>
                                    <br><small>İlişki: ${rel.relation_type}</small>
                                </div>`;
                            });
                        }
                        
                        if (context.documents.length > 0) {
                            html += '<h4>📄 İlgili Dokümanlar:</h4>';
                            context.documents.slice(0, 3).forEach((doc, index) => {
                                html += `<div class="entity">
                                    ${index + 1}. <a href="${doc.url}" target="_blank">${doc.title}</a>
                                </div>`;
                            });
                        }
                    }
                } else if (data.search_type === 'relationship') {
                    if (data.results.length === 0) {
                        html += '<p>❌ İlişki bulunamadı</p>';
                    } else {
                        data.results.slice(0, 10).forEach((rel, index) => {
                            html += `<div class="entity">
                                ${index + 1}. <strong>${rel.entity1}</strong> (${rel.entity1_type}) 
                                --[${rel.relation}]--> 
                                <strong>${rel.entity2}</strong> (${rel.entity2_type})
                            </div>`;
                        });
                    }
                } else if (data.search_type === 'document') {
                    if (data.results.length === 0) {
                        html += '<p>❌ Doküman bulunamadı</p>';
                    } else {
                        data.results.forEach((doc, index) => {
                            html += `<div class="entity">
                                ${index + 1}. <a href="${doc.url}" target="_blank">${doc.title}</a>
                                <br><small>📏 ${doc.content_length} karakter</small>
                            </div>`;
                        });
                    }
                }
                
                resultsDiv.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/graph")
async def graph_page():
    """Graf görselleştirme sayfası"""
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bursa Barosu - Bilgi Grafı</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                padding: 30px;
            }
            h1 {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            .control-group {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            label {
                font-weight: bold;
                color: #495057;
            }
            input, select {
                padding: 8px 12px;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                font-size: 14px;
            }
            button {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: background 0.3s;
            }
            button:hover {
                background: #0056b3;
            }
            #graph-container {
                width: 100%;
                height: 600px;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                background: #fff;
                position: relative;
                overflow: hidden;
            }
            .node {
                cursor: pointer;
                stroke-width: 2px;
            }
            .node.Person { fill: #ff6b6b; stroke: #e55555; }
            .node.Organization { fill: #4ecdc4; stroke: #45b7aa; }
            .node.Location { fill: #45b7d1; stroke: #3a9bc1; }
            .node.Date { fill: #96ceb4; stroke: #85b8a3; }
            .node.LegalTerm { fill: #feca57; stroke: #feb543; }
            .node.Entity { fill: #a8a8a8; stroke: #969696; }
            .link {
                stroke: #999;
                stroke-opacity: 0.6;
                stroke-width: 1.5px;
            }
            .node-label {
                font-size: 12px;
                font-weight: bold;
                text-anchor: middle;
                pointer-events: none;
                fill: #333;
            }
            .tooltip {
                position: absolute;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
                pointer-events: none;
                z-index: 1000;
                max-width: 200px;
            }
            .legend {
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(255,255,255,0.9);
                padding: 15px;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
            .legend-item {
                display: flex;
                align-items: center;
                margin-bottom: 5px;
            }
            .legend-color {
                width: 15px;
                height: 15px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .stats {
                text-align: center;
                margin-top: 20px;
                padding: 15px;
                background: #e9ecef;
                border-radius: 5px;
            }
            .loading {
                text-align: center;
                padding: 50px;
                font-size: 18px;
                color: #6c757d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🕸️ Bursa Barosu Bilgi Grafı</h1>
            
            <div class="controls">
                <div class="control-group">
                    <label for="nodeLimit">Düğüm Limiti:</label>
                    <input type="number" id="nodeLimit" value="50" min="10" max="200">
                    <button onclick="loadGraph()">Yenile</button>
                </div>
                <div class="control-group">
                    <label for="nodeType">Filtre:</label>
                    <select id="nodeType">
                        <option value="">Tümü</option>
                        <option value="Person">Kişiler</option>
                        <option value="Organization">Kurumlar</option>
                        <option value="Location">Yerler</option>
                        <option value="Date">Tarihler</option>
                        <option value="LegalTerm">Hukuki Terimler</option>
                    </select>
                    <button onclick="filterNodes()">Filtrele</button>
                </div>
                <div class="control-group">
                    <button onclick="centerGraph()">Merkeze Al</button>
                    <button onclick="resetZoom()">Yakınlaştırmayı Sıfırla</button>
                </div>
            </div>

            <div id="graph-container">
                <div class="loading" id="loading">Graf yükleniyor...</div>
                <div class="legend" id="legend" style="display: none;">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #ff6b6b;"></div>
                        <span>Kişiler</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #4ecdc4;"></div>
                        <span>Kurumlar</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #45b7d1;"></div>
                        <span>Yerler</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #96ceb4;"></div>
                        <span>Tarihler</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #feca57;"></div>
                        <span>Hukuki Terimler</span>
                    </div>
                </div>
            </div>

            <div class="stats" id="stats"></div>
        </div>

        <script>
            let svg, simulation, nodes, links, allNodes, allLinks;
            const width = 1140;
            const height = 600;

            // Tooltip oluştur
            const tooltip = d3.select("body").append("div")
                .attr("class", "tooltip")
                .style("opacity", 0);

            function initGraph() {
                const container = d3.select("#graph-container");
                
                svg = container.append("svg")
                    .attr("width", width)
                    .attr("height", height);

                // Zoom davranışı
                const zoom = d3.zoom()
                    .scaleExtent([0.1, 4])
                    .on("zoom", (event) => {
                        svg.selectAll("g").attr("transform", event.transform);
                    });

                svg.call(zoom);

                // Ana grup
                const g = svg.append("g");

                // Simülasyon
                simulation = d3.forceSimulation()
                    .force("link", d3.forceLink().id(d => d.id).distance(100))
                    .force("charge", d3.forceManyBody().strength(-300))
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .force("collision", d3.forceCollide().radius(30));
            }

            async function loadGraph() {
                const limit = document.getElementById('nodeLimit').value;
                document.getElementById('loading').style.display = 'block';
                document.getElementById('legend').style.display = 'none';

                try {
                    const response = await fetch(`/graph/data?limit=${limit}`);
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    
                    if (!data.nodes || !data.links) {
                        throw new Error('Geçersiz veri formatı: nodes veya links eksik');
                    }
                    
                    allNodes = data.nodes;
                    allLinks = data.links;
                    
                    console.log(`Graf yüklendi: ${allNodes.length} düğüm, ${allLinks.length} bağlantı`);
                    
                    renderGraph(allNodes, allLinks);
                    updateStats(data);
                    
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('legend').style.display = 'block';
                    
                } catch (error) {
                    console.error('Graf yüklenirken hata:', error);
                    document.getElementById('loading').innerHTML = `Graf yüklenirken hata oluştu!<br/><small>${error.message}</small>`;
                }
            }

            function renderGraph(nodeData, linkData) {
                console.log('renderGraph çağrıldı:', nodeData.length, 'düğüm,', linkData.length, 'bağlantı');
                
                // Node ID'lerinden node objelerine mapping oluştur
                const nodeMap = new Map();
                nodeData.forEach(node => nodeMap.set(node.id, node));
                
                // Link'lerdeki ID'leri node objelerine dönüştür
                const processedLinks = linkData.filter(link => {
                    const sourceNode = nodeMap.get(link.source);
                    const targetNode = nodeMap.get(link.target);
                    if (sourceNode && targetNode) {
                        link.source = sourceNode;
                        link.target = targetNode;
                        return true;
                    }
                    return false;
                });
                
                console.log('İşlenmiş linkler:', processedLinks.length);
                
                // Önceki grafı temizle
                svg.selectAll("g > *").remove();
                
                const g = svg.select("g");
                
                // Bağlantıları çiz
                const link = g.append("g")
                    .selectAll("line")
                    .data(processedLinks)
                    .enter().append("line")
                    .attr("class", "link")
                    .attr("stroke-width", d => Math.sqrt(2));

                // Düğümleri çiz
                const node = g.append("g")
                    .selectAll("circle")
                    .data(nodeData)
                    .enter().append("circle")
                    .attr("class", d => `node ${d.type}`)
                    .attr("r", d => {
                        // Düğüm boyutunu türüne göre ayarla
                        switch(d.type) {
                            case 'Person': return 12;
                            case 'Organization': return 15;
                            case 'Location': return 10;
                            case 'Date': return 8;
                            case 'LegalTerm': return 10;
                            default: return 8;
                        }
                    })
                    .on("mouseover", function(event, d) {
                        tooltip.transition().duration(200).style("opacity", .9);
                        tooltip.html(`<strong>${d.name}</strong><br/>Tür: ${d.type}<br/>ID: ${d.id}`)
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 28) + "px");
                    })
                    .on("mouseout", function(d) {
                        tooltip.transition().duration(500).style("opacity", 0);
                    })
                    .on("click", function(event, d) {
                        // Düğüme tıklandığında detay göster
                        alert(`${d.name} (${d.type}) hakkında daha fazla bilgi için arama yapın.`);
                    })
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                // Etiketler
                const labels = g.append("g")
                    .selectAll("text")
                    .data(nodeData)
                    .enter().append("text")
                    .attr("class", "node-label")
                    .text(d => d.name.length > 15 ? d.name.substring(0, 15) + "..." : d.name)
                    .attr("dy", 25);

                // Simülasyonu başlat
                simulation.nodes(nodeData).on("tick", ticked);
                simulation.force("link").links(processedLinks);
                simulation.alpha(1).restart();

                function ticked() {
                    link
                        .attr("x1", d => d.source.x)
                        .attr("y1", d => d.source.y)
                        .attr("x2", d => d.target.x)
                        .attr("y2", d => d.target.y);

                    node
                        .attr("cx", d => d.x)
                        .attr("cy", d => d.y);

                    labels
                        .attr("x", d => d.x)
                        .attr("y", d => d.y);
                }
            }

            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }

            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }

            function filterNodes() {
                const selectedType = document.getElementById('nodeType').value;
                
                if (!selectedType) {
                    renderGraph(allNodes, allLinks);
                    return;
                }

                const filteredNodes = allNodes.filter(n => n.type === selectedType);
                const nodeIds = new Set(filteredNodes.map(n => n.id));
                const filteredLinks = allLinks.filter(l => 
                    nodeIds.has(l.source.id || l.source) && 
                    nodeIds.has(l.target.id || l.target)
                );

                renderGraph(filteredNodes, filteredLinks);
            }

            function centerGraph() {
                svg.transition().duration(750).call(
                    d3.zoom().transform,
                    d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
                );
            }

            function resetZoom() {
                svg.transition().duration(750).call(
                    d3.zoom().transform,
                    d3.zoomIdentity
                );
            }

            function updateStats(data) {
                const statsDiv = document.getElementById('stats');
                const typeCount = {};
                
                data.nodes.forEach(node => {
                    typeCount[node.type] = (typeCount[node.type] || 0) + 1;
                });

                let statsHtml = `<strong>Graf İstatistikleri:</strong> `;
                statsHtml += `${data.total_nodes} düğüm, ${data.total_links} bağlantı<br/>`;
                
                for (const [type, count] of Object.entries(typeCount)) {
                    statsHtml += `${type}: ${count} | `;
                }
                
                statsDiv.innerHTML = statsHtml.slice(0, -3); // Son " | " kaldır
            }

            // Sayfa yüklendiğinde grafiği başlat
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM yüklendi, D3 var mı?', typeof d3 !== 'undefined');
                if (typeof d3 === 'undefined') {
                    document.getElementById('loading').innerHTML = 'D3.js kütüphanesi yüklenemedi!';
                    return;
                }
                initGraph();
                loadGraph();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/search", response_model=SearchResponse, tags=["Arama"])
async def search(
    query: str = Query(
        ..., 
        description="Arama sorgusu",
        example="Bursa Barosu kimdir"
    )
):
    """
    ## 🔍 Gelişmiş Semantik Arama
    
    Doğal dil kullanarak bilgi grafında akıllı arama yapar.
    
    ### Desteklenen Arama Türleri:
    - **Varlık Arama**: `Bursa`, `Ahmet Yılmaz`
    - **Varlık Detayları**: `Bursa Barosu kimdir`, `Ahmet Yılmaz hakkında`
    - **İlişki Arama**: `Bursa ile İstanbul arasındaki ilişki`
    - **Doküman Arama**: `avukat dokümanları`, `hukuk belgeleri`
    
    ### Örnek Sorgular:
    - `Bursa Barosu`
    - `Bursa Barosu kimdir`
    - `avukat dokümanları`
    - `Bursa ile İstanbul arasındaki ilişki`
    """
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        results = search_engine.advanced_search(query)
        return SearchResponse(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Arama hatası: {str(e)}")

@app.get("/entities", response_model=List[EntityResponse], tags=["Varlık Arama"])
async def search_entities(
    query: str = Query(..., description="Arama sorgusu", example="Bursa"),
    entity_type: Optional[str] = Query(None, description="Varlık türü filtresi", example="Person"),
    limit: int = Query(10, description="Maksimum sonuç sayısı", ge=1, le=100)
):
    """
    ## 👥 Varlık Arama
    
    Belirli varlık türlerinde arama yapar.
    
    ### Desteklenen Varlık Türleri:
    - **Person**: Kişi isimleri
    - **Organization**: Kurum ve kuruluşlar
    - **Location**: Yer isimleri
    - **Date**: Tarihler
    - **LegalTerm**: Hukuki terimler
    
    ### Örnekler:
    - `query=Bursa&entity_type=Location`
    - `query=Barosu&entity_type=Organization`
    - `query=Ahmet&entity_type=Person`
    """
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        entities = search_engine.search_entities(query, entity_type, limit)
        return [EntityResponse(**entity) for entity in entities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Varlık arama hatası: {str(e)}")

@app.get("/relationships", response_model=List[RelationshipResponse])
async def search_relationships(
    entity1: str = Query(..., description="İlk varlık"),
    entity2: Optional[str] = Query(None, description="İkinci varlık"),
    relation_type: Optional[str] = Query(None, description="İlişki türü")
):
    """İlişki arama"""
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        relationships = search_engine.find_relationships(entity1, entity2, relation_type)
        return [RelationshipResponse(**rel) for rel in relationships]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İlişki arama hatası: {str(e)}")

@app.get("/documents", response_model=List[DocumentResponse])
async def search_documents(
    query: str = Query(..., description="Arama sorgusu"),
    limit: int = Query(10, description="Maksimum sonuç sayısı")
):
    """Doküman arama"""
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        documents = search_engine.search_documents(query, limit)
        return [DocumentResponse(**doc) for doc in documents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Doküman arama hatası: {str(e)}")

@app.get("/entity/{entity_name}")
async def get_entity_context(entity_name: str):
    """Varlık bağlamı getir"""
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        context = search_engine.get_entity_context(entity_name)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Varlık bağlamı hatası: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Graf istatistikleri"""
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        stats = search_engine.get_statistics()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İstatistik hatası: {str(e)}")

@app.get("/graph/data", tags=["Graf Görselleştirme"])
async def get_graph_data(
    limit: int = Query(100, description="Maksimum düğüm sayısı", ge=10, le=2000)
):
    """
    ## 🕸️ Graf Görselleştirme Verileri
    
    İnteraktif graf görselleştirme için düğüm ve bağlantı verilerini döndürür.
    
    ### Dönen Veri Yapısı:
    - **nodes**: Düğüm listesi (id, name, type, group)
    - **links**: Bağlantı listesi (source, target, type)
    - **total_nodes**: Toplam düğüm sayısı
    - **total_links**: Toplam bağlantı sayısı
    
    ### Kullanım:
    Bu endpoint'i kullanarak D3.js ile interaktif graf oluşturabilirsiniz.
    """
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        # Düğümleri getir
        nodes_query = """
        MATCH (n) 
        WHERE NOT n:Document
        RETURN n.name as name, labels(n)[0] as type, id(n) as id
        LIMIT $limit
        """
        
        # Bağlantıları getir
        edges_query = """
        MATCH (a)-[r]->(b) 
        WHERE NOT a:Document AND NOT b:Document
        RETURN id(a) as source, id(b) as target, type(r) as type
        LIMIT $limit
        """
        
        nodes_result = search_engine.driver.execute_query(nodes_query, limit=limit)
        edges_result = search_engine.driver.execute_query(edges_query, limit=limit)
        
        nodes = []
        for record in nodes_result.records:
            nodes.append({
                "id": record["id"],
                "name": record["name"] or "Unnamed",
                "type": record["type"] or "Entity",
                "group": record["type"] or "Entity"
            })
        
        edges = []
        for record in edges_result.records:
            edges.append({
                "source": record["source"],
                "target": record["target"],
                "type": record["type"] or "CONNECTED"
            })
        
        return {
            "nodes": nodes,
            "links": edges,
            "total_nodes": len(nodes),
            "total_links": len(edges)
        }
        
    except Exception as e:
        logger.error(f"Graf verileri alınırken hata: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "search_engine": "active" if search_engine else "inactive"
    }

@app.get("/cache/stats", tags=["Sistem"])
async def get_cache_stats():
    """
    ## 🗄️ Cache İstatistikleri
    
    Sistemin cache performansını gösterir.
    
    ### Dönen Bilgiler:
    - **memory_cache_size**: Bellekteki cache boyutu
    - **memory_cache_maxsize**: Maksimum cache boyutu
    - **redis_enabled**: Redis aktif mi?
    - **default_ttl**: Varsayılan cache süresi
    """
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        cache_stats = search_engine.cache.get_stats()
        return cache_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache istatistik hatası: {str(e)}")

@app.delete("/cache/clear", tags=["Sistem"])
async def clear_cache():
    """
    ## 🗑️ Cache Temizle
    
    Tüm cache'i temizler. Performans testleri için kullanışlıdır.
    """
    if not search_engine:
        raise HTTPException(status_code=500, detail="Search engine başlatılamadı")
    
    try:
        success = search_engine.cache.clear()
        return {
            "success": success,
            "message": "Cache başarıyla temizlendi" if success else "Cache temizleme başarısız"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache temizleme hatası: {str(e)}")

@app.get("/updater/status", tags=["Otomatik Güncelleme"])
async def get_updater_status():
    """
    ## 🔄 Otomatik Güncelleme Durumu
    
    Otomatik veri güncelleme sisteminin durumunu gösterir.
    
    ### Dönen Bilgiler:
    - **is_running**: Scheduler aktif mi?
    - **update_interval_hours**: Güncelleme aralığı
    - **next_scheduled_update**: Bir sonraki güncelleme zamanı
    - **stats**: Güncelleme istatistikleri
    """
    try:
        updater = get_updater()
        status = updater.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Updater durum hatası: {str(e)}")

@app.post("/updater/start", tags=["Otomatik Güncelleme"])
async def start_updater():
    """
    ## ▶️ Otomatik Güncellemeyi Başlat
    
    Scheduler'ı başlatır ve düzenli güncellemeleri etkinleştirir.
    """
    try:
        updater = get_updater()
        if updater.is_running:
            return {"message": "Updater zaten çalışıyor", "status": "already_running"}
        
        updater.start_scheduler()
        return {"message": "Updater başlatıldı", "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Updater başlatma hatası: {str(e)}")

@app.post("/updater/stop", tags=["Otomatik Güncelleme"])
async def stop_updater():
    """
    ## ⏹️ Otomatik Güncellemeyi Durdur
    
    Scheduler'ı durdurur ve düzenli güncellemeleri devre dışı bırakır.
    """
    try:
        updater = get_updater()
        if not updater.is_running:
            return {"message": "Updater zaten durmuş", "status": "already_stopped"}
        
        updater.stop_scheduler()
        return {"message": "Updater durduruldu", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Updater durdurma hatası: {str(e)}")

@app.post("/updater/force-update", tags=["Otomatik Güncelleme"])
async def force_update():
    """
    ## 🔄 Zorla Güncelleme
    
    Zamanlanmış güncellemeyi beklemeden hemen güncelleme yapar.
    
    **Dikkat**: Bu işlem birkaç dakika sürebilir.
    """
    try:
        updater = get_updater()
        result = updater.force_update()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zorla güncelleme hatası: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
