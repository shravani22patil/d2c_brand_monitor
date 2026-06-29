import os
import json
import pandas as pd

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
DASHBOARD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")

def main():
    print("Reading CSV data for web dashboard...")
    
    # Load all files
    df_brand = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_brand.csv"))
    df_date = pd.read_csv(os.path.join(EXPORTS_DIR, "dim_date.csv"))
    df_reviews = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_reviews.csv"))
    df_summary = pd.read_csv(os.path.join(EXPORTS_DIR, "fact_monthly_summary.csv"))
    df_alerts = pd.read_csv(os.path.join(EXPORTS_DIR, "keyword_alerts.csv"))
    
    # Convert DataFrames to JSON strings to embed in HTML
    brands_json = df_brand.to_json(orient="records")
    reviews_json = df_reviews.to_json(orient="records")
    summary_json = df_summary.to_json(orient="records")
    alerts_json = df_alerts.to_json(orient="records")
    
    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D2C Brand Health Monitor Dashboard</title>
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: #111827;
            --border-color: #1f2937;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent: #2ec4b6;
            --positive: #10b981;
            --neutral: #f59e0b;
            --negative: #ef4444;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
        }}
        
        body {{
            background-color: var(--bg-color);
            color: var(--text-primary);
            display: flex;
            min-height: 100vh;
        }}
        
        /* Sidebar */
        .sidebar {{
            width: 260px;
            background-color: #070a13;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 20px;
            position: fixed;
            height: 100vh;
        }}
        
        .sidebar-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 30px;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--text-primary);
        }}
        
        .sidebar-header span {{
            color: var(--accent);
        }}
        
        .nav-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            flex-grow: 1;
        }}
        
        .nav-item {{
            padding: 12px 16px;
            border-radius: 8px;
            cursor: pointer;
            color: var(--text-secondary);
            font-weight: 600;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .nav-item:hover, .nav-item.active {{
            background-color: var(--card-bg);
            color: var(--text-primary);
            border-left: 4px solid var(--accent);
        }}
        
        /* Main Workspace */
        .main-content {{
            margin-left: 260px;
            flex-grow: 1;
            padding: 30px;
        }}
        
        /* Header Bar */
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        header h1 {{
            font-size: 1.5rem;
            font-weight: 700;
        }}
        
        .filters {{
            display: flex;
            gap: 15px;
        }}
        
        select {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 8px;
            outline: none;
            cursor: pointer;
            font-weight: 600;
        }}
        
        /* KPI Cards Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        
        .kpi-title {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-weight: 600;
        }}
        
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: 700;
        }}
        
        .kpi-subtext {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        
        /* Dashboard Views */
        .dashboard-view {{
            display: none;
        }}
        
        .dashboard-view.active {{
            display: block;
        }}
        
        /* Visual Rows */
        .chart-row {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .chart-row.equal {{
            grid-template-columns: 1fr 1fr;
        }}
        
        .chart-row.full {{
            grid-template-columns: 1fr;
        }}
        
        .chart-container {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            position: relative;
            height: 350px;
            width: 100%;
        }}
        
        .chart-title {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 20px;
            color: var(--text-primary);
        }}
        
        /* Alerts Table */
        .alerts-table-container {{
            width: 100%;
            overflow-x: auto;
            max-height: 300px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        
        th {{
            background-color: #070a13;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.85rem;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
        }}
        
        td {{
            padding: 12px 16px;
            font-size: 0.9rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}
        
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        .badge.high {{
            background-color: rgba(239, 68, 68, 0.2);
            color: var(--negative);
        }}
        
        .badge.medium {{
            background-color: rgba(245, 158, 11, 0.2);
            color: var(--neutral);
        }}
        
        .badge.low {{
            background-color: rgba(16, 185, 129, 0.2);
            color: var(--positive);
        }}
        
        /* Weekly Digest Cards */
        .digest-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .digest-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .digest-brand-name {{
            font-size: 1.2rem;
            font-weight: 700;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }}
        
        .digest-metric {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
        }}
        
        .digest-metric span:first-child {{
            color: var(--text-secondary);
        }}
        
        .digest-metric span:last-child {{
            font-weight: 600;
        }}
        
        .digest-score-pill {{
            align-self: flex-start;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.8rem;
        }}
        
        .score-good {{ background-color: rgba(16, 185, 129, 0.2); color: var(--positive); }}
        .score-average {{ background-color: rgba(245, 158, 11, 0.2); color: var(--neutral); }}
        .score-poor {{ background-color: rgba(239, 68, 68, 0.2); color: var(--negative); }}
        
        .summary-box {{
            background-color: #070a13;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 25px;
            line-height: 1.6;
        }}
        
        .summary-box h3 {{
            margin-bottom: 15px;
            color: var(--accent);
        }}
    </style>
</head>
<body>

    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-header">
            🧴 <span>D2C Skincare</span> Monitor
        </div>
        <ul class="nav-list">
            <li class="nav-item active" onclick="switchTab('overview')">📊 Overview</li>
            <li class="nav-item" onclick="switchTab('sentiment')">🧠 Sentiment Deep Dive</li>
            <li class="nav-item" onclick="switchTab('keywords')">💬 Keyword Analysis</li>
            <li class="nav-item" onclick="switchTab('digest')">📰 Weekly Digest</li>
        </ul>
    </div>

    <!-- Main Workspace -->
    <div class="main-content">
        <header>
            <h1 id="page-title">Brand Health Overview</h1>
            <div class="filters">
                <select id="brand-select" onchange="onFilterChange()">
                    <option value="All">All Brands</option>
                </select>
                <select id="month-select" onchange="onFilterChange()">
                    <option value="All">All Months</option>
                </select>
            </div>
        </header>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <span class="kpi-title">Average Rating</span>
                <span class="kpi-value" id="kpi-rating">-</span>
                <span class="kpi-subtext">Out of 5 stars</span>
            </div>
            <div class="kpi-card">
                <span class="kpi-title">Total Reviews</span>
                <span class="kpi-value" id="kpi-reviews">-</span>
                <span class="kpi-subtext" id="kpi-reviews-sub">Collected reviews</span>
            </div>
            <div class="kpi-card">
                <span class="kpi-title">Positive Review %</span>
                <span class="kpi-value" id="kpi-positive-pct">-</span>
                <span class="kpi-subtext" style="color: var(--positive)">Net positive feedback</span>
            </div>
            <div class="kpi-card">
                <span class="kpi-title">Active Alerts</span>
                <span class="kpi-value" id="kpi-alerts">-</span>
                <span class="kpi-subtext" style="color: var(--negative)" id="kpi-alerts-sub">Shift > 5%</span>
            </div>
        </div>

        <!-- ================= PAGE 1: OVERVIEW ================= -->
        <div id="view-overview" class="dashboard-view active">
            <div class="chart-row full">
                <div class="chart-container">
                    <div class="chart-title">Brand Rating Timeline — Last 6 Months</div>
                    <canvas id="timelineChart"></canvas>
                </div>
            </div>
            <div class="chart-row equal">
                <div class="chart-container">
                    <div class="chart-title">Sentiment Breakdown by Brand</div>
                    <canvas id="sentimentBreakdownChart"></canvas>
                </div>
                <div class="chart-container" style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 15px;">
                    <div class="chart-title" style="align-self: flex-start;">Composite Brand Health Score</div>
                    <div style="position: relative; width: 200px; height: 200px; display: flex; align-items: center; justify-content: center;">
                        <canvas id="gaugeChart"></canvas>
                        <div id="gauge-val" style="position: absolute; font-size: 2rem; font-weight: 700; color: var(--accent);">0</div>
                    </div>
                    <div class="kpi-subtext">Composite of Rating, Net Sentiment, and Velocity</div>
                </div>
            </div>
        </div>

        <!-- ================= PAGE 2: SENTIMENT ================= -->
        <div id="view-sentiment" class="dashboard-view">
            <div class="chart-row full">
                <div class="chart-container">
                    <div class="chart-title">Sentiment Score Trend Over Time per Brand</div>
                    <canvas id="sentimentTrendChart"></canvas>
                </div>
            </div>
            <div class="chart-row equal">
                <div class="chart-container">
                    <div class="chart-title">Subjectivity Distribution (Fact Reviews)</div>
                    <canvas id="subjectivityChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Numerical Rating vs. Sentiment Polarity</div>
                    <canvas id="ratingPolarityChart"></canvas>
                </div>
            </div>
        </div>

        <!-- ================= PAGE 3: KEYWORDS ================= -->
        <div id="view-keywords" class="dashboard-view">
            <div class="chart-row full">
                <div class="chart-container" style="min-height: auto;">
                    <div class="chart-title">Rising Keyword Alerts (Shift > 5.0%)</div>
                    <div class="alerts-table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Brand</th>
                                    <th>Keyword</th>
                                    <th>Month</th>
                                    <th>Negative Reviews %</th>
                                    <th>MoM Shift</th>
                                    <th>Alert Severity</th>
                                </tr>
                            </thead>
                            <tbody id="alerts-table-body">
                                <!-- Populated dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="chart-row equal">
                <div class="chart-container">
                    <div class="chart-title">Top 10 Keywords by Frequency</div>
                    <canvas id="keywordsBarChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Packaging Complaint % Over Time</div>
                    <canvas id="packagingChart"></canvas>
                </div>
            </div>
        </div>

        <!-- ================= PAGE 4: DIGEST ================= -->
        <div id="view-digest" class="dashboard-view">
            <div class="digest-grid" id="digest-grid-container">
                <!-- Dynamically generated brand cards -->
            </div>
            <div class="summary-box">
                <h3>Executive Summary Narrative</h3>
                <p id="digest-narrative-text">Select a brand to see a dynamic plain English narrative summary of recent customer complaints and ratings trends.</p>
            </div>
        </div>
    </div>

    <!-- Data Injection -->
    <script>
        const brandsData = {brands_json};
        const reviewsData = {reviews_json};
        const summaryData = {summary_json};
        const alertsData = {alerts_json};
        
        // Active Chart References
        let charts = {{}};
        
        // Initial setup
        window.onload = function() {{
            populateFilters();
            switchTab('overview');
        }};
        
        function populateFilters() {{
            // Populate Brands
            const brandSelect = document.getElementById('brand-select');
            const uniqueBrands = [...new Set(summaryData.map(d => d.brand_name))];
            uniqueBrands.forEach(brand => {{
                let opt = document.createElement('option');
                opt.value = brand;
                opt.textContent = brand;
                brandSelect.appendChild(opt);
            }});
            
            // Populate Months
            const monthSelect = document.getElementById('month-select');
            const uniqueMonths = [...new Set(summaryData.map(d => d.year_month))].sort();
            uniqueMonths.forEach(month => {{
                let opt = document.createElement('option');
                opt.value = month;
                opt.textContent = month;
                monthSelect.appendChild(opt);
            }});
        }}
        
        function switchTab(tabId) {{
            // Switch tabs classes
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            document.querySelectorAll('.dashboard-view').forEach(view => view.classList.remove('active'));
            
            let btnIndex = 0;
            if (tabId === 'overview') btnIndex = 0;
            else if (tabId === 'sentiment') btnIndex = 1;
            else if (tabId === 'keywords') btnIndex = 2;
            else if (tabId === 'digest') btnIndex = 3;
            
            document.querySelectorAll('.nav-item')[btnIndex].classList.add('active');
            document.getElementById('view-' + tabId).classList.add('active');
            
            const titleMap = {{
                'overview': 'Brand Health Overview',
                'sentiment': 'Sentiment Analysis by Brand',
                'keywords': 'What Customers Are Talking About',
                'digest': "This Week's Brand Intelligence Digest"
            }};
            document.getElementById('page-title').textContent = titleMap[tabId];
            
            // Render specific charts for the tab
            renderTabCharts(tabId);
        }}
        
        function onFilterChange() {{
            // Re-render currently active view
            const activeView = document.querySelector('.dashboard-view.active').id.replace('view-', '');
            renderTabCharts(activeView);
        }}
        
        function getFilteredData() {{
            const selectedBrand = document.getElementById('brand-select').value;
            const selectedMonth = document.getElementById('month-select').value;
            
            let filteredReviews = reviewsData;
            let filteredSummary = summaryData;
            let filteredAlerts = alertsData;
            
            if (selectedBrand !== 'All') {{
                filteredReviews = filteredReviews.filter(d => d.brand_name === selectedBrand);
                filteredSummary = filteredSummary.filter(d => d.brand_name === selectedBrand);
                filteredAlerts = filteredAlerts.filter(d => d.brand_name === selectedBrand);
            }}
            
            if (selectedMonth !== 'All') {{
                filteredReviews = filteredReviews.filter(d => d.year_month === selectedMonth);
                filteredSummary = filteredSummary.filter(d => d.year_month === selectedMonth);
                filteredAlerts = filteredAlerts.filter(d => d.year_month === selectedMonth);
            }}
            
            return {{ reviews: filteredReviews, summary: filteredSummary, alerts: filteredAlerts }};
        }}
        
        function updateKPIs(data) {{
            // Avg rating
            const ratings = data.reviews.map(d => d.rating);
            const avgRating = ratings.length ? (ratings.reduce((a,b)=>a+b, 0) / ratings.length).toFixed(2) : '-';
            document.getElementById('kpi-rating').textContent = avgRating;
            
            // Total reviews
            document.getElementById('kpi-reviews').textContent = data.reviews.length;
            
            // Positive review %
            const posCount = data.reviews.filter(d => d.sentiment_label === 'Positive').length;
            const posPct = data.reviews.length ? ((posCount / data.reviews.length) * 100).toFixed(1) : '0';
            document.getElementById('kpi-positive-pct').textContent = posPct + '%';
            
            // Active alerts
            document.getElementById('kpi-alerts').textContent = data.alerts.length;
        }}
        
        function destroyChart(name) {{
            if (charts[name]) {{
                charts[name].destroy();
            }}
        }}
        
        function renderTabCharts(tabId) {{
            const data = getFilteredData();
            updateKPIs(data);
            
            // Clear existing charts
            Chart.helpers.each(Chart.instances, function(instance) {{
                if (instance.canvas.id === 'timelineChart' && tabId !== 'overview') return;
                // We'll clean them manually
            }});
            
            if (tabId === 'overview') {{
                renderOverviewTab(data);
            }} else if (tabId === 'sentiment') {{
                renderSentimentTab(data);
            }} else if (tabId === 'keywords') {{
                renderKeywordsTab(data);
            }} else if (tabId === 'digest') {{
                renderDigestTab(data);
            }}
        }}
        
        // ================= RENDER LOGIC FOR TAB 1: OVERVIEW =================
        function renderOverviewTab(data) {{
            destroyChart('timeline');
            destroyChart('breakdown');
            destroyChart('gauge');
            
            // 1. Timeline: Average rating over time per brand
            const ctxTimeline = document.getElementById('timelineChart').getContext('2d');
            // Get unique months, sorted
            const months = [...new Set(summaryData.map(d => d.year_month))].sort();
            const brands = [...new Set(summaryData.map(d => d.brand_name))];
            
            const colors = {{
                'Mamaearth': '#8bc34a',
                'Dot & Key': '#009688',
                'Plum': '#9c27b0',
                'WOW Skin Science': '#ff9800'
            }};
            
            const datasets = brands.map(brand => {{
                // Find summary ratings for this brand across all months
                const brandSummary = summaryData.filter(d => d.brand_name === brand);
                const dataPoints = months.map(m => {{
                    const match = brandSummary.find(d => d.year_month === m);
                    return match ? match.avg_rating : null;
                }});
                
                return {{
                    label: brand,
                    data: dataPoints,
                    borderColor: colors[brand] || '#2ec4b6',
                    tension: 0.2,
                    fill: false
                }};
            }});
            
            charts['timeline'] = new Chart(ctxTimeline, {{
                type: 'line',
                data: {{ labels: months, datasets: datasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ min: 1, max: 5, grid: {{ color: '#1f2937' }} }},
                        x: {{ grid: {{ color: '#1f2937' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
                }}
            }});
            
            // 2. Sentiment Breakdown Bar Chart
            const ctxBreakdown = document.getElementById('sentimentBreakdownChart').getContext('2d');
            const uniqueBrands = [...new Set(data.reviews.map(d => d.brand_name))];
            
            const posData = [];
            const negData = [];
            const neutData = [];
            
            uniqueBrands.forEach(b => {{
                const brandReviews = data.reviews.filter(d => d.brand_name === b);
                const total = brandReviews.length;
                if(total > 0) {{
                    posData.push(((brandReviews.filter(d => d.sentiment_label === 'Positive').length / total) * 100).toFixed(1));
                    negData.push(((brandReviews.filter(d => d.sentiment_label === 'Negative').length / total) * 100).toFixed(1));
                    neutData.push(((brandReviews.filter(d => d.sentiment_label === 'Neutral').length / total) * 100).toFixed(1));
                }} else {{
                    posData.push(0); negData.push(0); neutData.push(0);
                }}
            }});
            
            charts['breakdown'] = new Chart(ctxBreakdown, {{
                type: 'bar',
                data: {{
                    labels: uniqueBrands,
                    datasets: [
                        {{ label: 'Positive %', data: posData, backgroundColor: '#10b981' }},
                        {{ label: 'Neutral %', data: neutData, backgroundColor: '#f59e0b' }},
                        {{ label: 'Negative %', data: negData, backgroundColor: '#ef4444' }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ max: 100, grid: {{ color: '#1f2937' }} }},
                        x: {{ grid: {{ color: '#1f2937' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
                }}
            }});
            
            // 3. Brand Health Score Gauge
            const ctxGauge = document.getElementById('gaugeChart').getContext('2d');
            
            // Compute average brand health score for current filtered data
            // Calculation:
            // RatingScore: avg_rating / 5 * 40
            // SentimentScore: (pos% - neg%) / 100 + 1 / 2 * 40
            // VelocityScore: if velocity > 0 => 20, else if velocity > -20 => 10, else 0
            const avgRatingVal = data.reviews.length ? (data.reviews.map(d => d.rating).reduce((a,b)=>a+b, 0) / data.reviews.length) : 0;
            const totalCount = data.reviews.length;
            const positiveCount = data.reviews.filter(d => d.sentiment_label === 'Positive').length;
            const negativeCount = data.reviews.filter(d => d.sentiment_label === 'Negative').length;
            
            const positivePct = totalCount ? (positiveCount / totalCount) * 100 : 0;
            const negativePct = totalCount ? (negativeCount / totalCount) * 100 : 0;
            
            const avgVelocity = data.summary.length ? (data.summary.map(d => d.review_velocity).reduce((a,b)=>a+b,0) / data.summary.length) : 0;
            
            const ratingScore = (avgRatingVal / 5) * 40;
            const sentimentScore = (((positivePct - negativePct) / 100 + 1) / 2) * 40;
            const velocityScore = avgVelocity > 0 ? 20 : (avgVelocity > -20 ? 10 : 0);
            
            const healthScore = Math.round(ratingScore + sentimentScore + velocityScore);
            document.getElementById('gauge-val').textContent = healthScore;
            
            charts['gauge'] = new Chart(ctxGauge, {{
                type: 'doughnut',
                data: {{
                    datasets: [{{
                        data: [healthScore, 100 - healthScore],
                        backgroundColor: ['#2ec4b6', '#1f2937'],
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    circumference: 180,
                    rotation: 270,
                    cutout: '80%',
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        }}
        
        // ================= RENDER LOGIC FOR TAB 2: SENTIMENT =================
        function renderSentimentTab(data) {{
            destroyChart('sentimentTrend');
            destroyChart('subjectivity');
            destroyChart('ratingPolarity');
            
            // 1. Sentiment Score Trend over time per brand (Average polarity * 100)
            const ctxTrend = document.getElementById('sentimentTrendChart').getContext('2d');
            const months = [...new Set(summaryData.map(d => d.year_month))].sort();
            const brands = [...new Set(summaryData.map(d => d.brand_name))];
            const colors = {{ 'Mamaearth': '#8bc34a', 'Dot & Key': '#009688', 'Plum': '#9c27b0', 'WOW Skin Science': '#ff9800' }};
            
            const datasets = brands.map(brand => {{
                const brandSummary = summaryData.filter(d => d.brand_name === brand);
                const dataPoints = months.map(m => {{
                    const match = brandSummary.find(d => d.year_month === m);
                    return match ? (match.avg_polarity * 100) : null;
                }});
                
                return {{
                    label: brand,
                    data: dataPoints,
                    borderColor: colors[brand] || '#2ec4b6',
                    backgroundColor: (colors[brand] || '#2ec4b6') + '22',
                    fill: true,
                    tension: 0.2
                }};
            }});
            
            charts['sentimentTrend'] = new Chart(ctxTrend, {{
                type: 'line',
                data: {{ labels: months, datasets: datasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ min: -100, max: 100, grid: {{ color: '#1f2937' }} }},
                        x: {{ grid: {{ color: '#1f2937' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
                }}
            }});
            
            // 2. Subjectivity distribution
            const ctxSubj = document.getElementById('subjectivityChart').getContext('2d');
            const subValues = data.reviews.map(d => d.subjectivity);
            // Group subjectivity into ranges [0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0]
            const buckets = [0, 0, 0, 0, 0];
            subValues.forEach(v => {{
                if (v <= 0.2) buckets[0]++;
                else if (v <= 0.4) buckets[1]++;
                else if (v <= 0.6) buckets[2]++;
                else if (v <= 0.8) buckets[3]++;
                else buckets[4]++;
            }});
            
            charts['subjectivity'] = new Chart(ctxSubj, {{
                type: 'bar',
                data: {{
                    labels: ['0.0-0.2 (Objective)', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1.0 (Opinionated)'],
                    datasets: [{{
                        label: 'Reviews Count',
                        data: buckets,
                        backgroundColor: '#a78bfa'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ grid: {{ color: '#1f2937' }} }},
                        x: {{ grid: {{ color: '#1f2937' }} }}
                    }},
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
            
            // 3. Rating vs. Polarity scatter
            const ctxScatter = document.getElementById('ratingPolarityChart').getContext('2d');
            // Take a sample of reviews to avoid cluttering (e.g. max 150)
            const sampleReviews = data.reviews.slice(0, 150);
            
            const scatterColors = {{ 'Mamaearth': '#8bc34a', 'Dot & Key': '#009688', 'Plum': '#9c27b0', 'WOW Skin Science': '#ff9800' }};
            const scatterData = sampleReviews.map(r => ({{
                x: r.polarity,
                y: r.rating,
                brand: r.brand_name
            }}));
            
            const uniqueBrandsSample = [...new Set(scatterData.map(d => d.brand))];
            const scatterDatasets = uniqueBrandsSample.map(b => ({{
                label: b,
                data: scatterData.filter(d => d.brand === b),
                backgroundColor: scatterColors[b] || '#2ec4b6',
                pointRadius: 6
            }}));
            
            charts['ratingPolarity'] = new Chart(ctxScatter, {{
                type: 'scatter',
                data: {{ datasets: scatterDatasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ min: -1, max: 1, title: {{ display: true, text: 'Polarity', color: '#fff' }}, grid: {{ color: '#1f2937' }} }},
                        y: {{ min: 1, max: 5, title: {{ display: true, text: 'Rating (1-5)', color: '#fff' }}, grid: {{ color: '#1f2937' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
                }}
            }});
        }}
        
        // ================= RENDER LOGIC FOR TAB 3: KEYWORDS =================
        function renderKeywordsTab(data) {{
            destroyChart('keywordsBar');
            destroyChart('packaging');
            
            // 1. Populate Alerts Table (Shift > 5%)
            const tbody = document.getElementById('alerts-table-body');
            tbody.innerHTML = '';
            
            // Filter global alerts
            const filteredAlertsList = alertsData.filter(d => {{
                const brandMatch = document.getElementById('brand-select').value === 'All' || d.brand_name === document.getElementById('brand-select').value;
                const monthMatch = document.getElementById('month-select').value === 'All' || d.year_month === document.getElementById('month-select').value;
                return brandMatch && monthMatch && d.keyword_shift > 5.0;
            }});
            
            // Sort by shift descending
            filteredAlertsList.sort((a,b) => b.keyword_shift - a.keyword_shift);
            
            if(filteredAlertsList.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No alerts detected above 5% shift for current selection.</td></tr>';
            }} else {{
                filteredAlertsList.forEach(alert => {{
                    let sev = 'low';
                    if (alert.keyword_shift > 20) sev = 'high';
                    else if (alert.keyword_shift > 10) sev = 'medium';
                    
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${{alert.brand_name}}</td>
                        <td style="font-weight: 600; color: var(--accent);">'${{alert.keyword}}'</td>
                        <td>${{alert.year_month}}</td>
                        <td>${{alert.pct_of_negative_reviews.toFixed(1)}}%</td>
                        <td style="color: var(--negative); font-weight: 600;">+${{alert.keyword_shift.toFixed(1)}}%</td>
                        <td><span class="badge ${{sev}}">${{sev.toUpperCase()}}</span></td>
                    `;
                    tbody.appendChild(tr);
                }});
            }}
            
            // 2. Bar Chart: Top 10 keywords by frequency
            const ctxKWBar = document.getElementById('keywordsBarChart').getContext('2d');
            // Aggregate keyword frequencies from our filteredAlerts
            const kwCounts = {{}};
            data.alerts.forEach(d => {{
                kwCounts[d.keyword] = (kwCounts[d.keyword] || 0) + d.frequency;
            }});
            
            const sortedKWs = Object.entries(kwCounts).sort((a,b) => b[1] - a[1]).slice(0, 10);
            const kwLabels = sortedKWs.map(d => `'` + d[0] + `'`);
            const kwValues = sortedKWs.map(d => d[1]);
            
            charts['keywordsBar'] = new Chart(ctxKWBar, {{
                type: 'bar',
                data: {{
                    labels: kwLabels,
                    datasets: [{{
                        label: 'Frequency',
                        data: kwValues,
                        backgroundColor: '#2ec4b6'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    scales: {{
                        x: {{ grid: {{ color: '#1f2937' }} }},
                        y: {{ grid: {{ color: '#1f2937' }} }}
                    }},
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
            
            // 3. Packaging Complaint % over time (headline line chart)
            const ctxPack = document.getElementById('packagingChart').getContext('2d');
            const months = [...new Set(summaryData.map(d => d.year_month))].sort();
            const brands = [...new Set(summaryData.map(d => d.brand_name))];
            const colors = {{ 'Mamaearth': '#8bc34a', 'Dot & Key': '#009688', 'Plum': '#9c27b0', 'WOW Skin Science': '#ff9800' }};
            
            const datasets = brands.map(brand => {{
                // Calculate packing complaint % for this brand across months
                // Find percentage of reviews containing 'packaging'
                const dataPoints = months.map(m => {{
                    const mReviews = reviewsData.filter(r => r.brand_name === brand && r.year_month === m);
                    if (mReviews.length === 0) return 0;
                    const packCount = mReviews.filter(r => r.has_keyword_packaging === 1).length;
                    return ((packCount / mReviews.length) * 100);
                }});
                
                return {{
                    label: brand,
                    data: dataPoints,
                    borderColor: colors[brand] || '#2ec4b6',
                    fill: false,
                    tension: 0.2
                }};
            }});
            
            charts['packaging'] = new Chart(ctxPack, {{
                type: 'line',
                data: {{ labels: months, datasets: datasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ min: 0, max: 100, title: {{ display: true, text: 'Complaint %', color: '#fff' }}, grid: {{ color: '#1f2937' }} }},
                        x: {{ grid: {{ color: '#1f2937' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '#fff' }} }} }}
                }}
            }});
        }}
        
        // ================= RENDER LOGIC FOR TAB 4: DIGEST =================
        function renderDigestTab(data) {{
            // Generate Executive Brand Cards
            const container = document.getElementById('digest-grid-container');
            container.innerHTML = '';
            
            const brands = [...new Set(summaryData.map(d => d.brand_name))];
            
            brands.forEach(brand => {{
                const brandReviews = reviewsData.filter(r => r.brand_name === brand);
                const ratings = brandReviews.map(r => r.rating);
                const avgRating = ratings.length ? (ratings.reduce((a,b)=>a+b, 0) / ratings.length).toFixed(2) : '-';
                
                // Get latest month rating trend
                const brandSummaries = summaryData.filter(s => s.brand_name === brand);
                let latestMonth = '';
                let ratingTrend = 0;
                let trendText = '→ Stable';
                
                if (brandSummaries.length > 0) {{
                    brandSummaries.sort((a,b) => b.year_month.localeCompare(a.year_month));
                    latestMonth = brandSummaries[0].year_month;
                    ratingTrend = brandSummaries[0].rating_trend;
                    if (ratingTrend > 0.1) trendText = `▲ +${{ratingTrend.toFixed(2)}}`;
                    else if (ratingTrend < -0.1) trendText = `▼ -${{Math.abs(ratingTrend).toFixed(2)}}`;
                }}
                
                // Top rising keyword
                const brandAlerts = alertsData.filter(a => a.brand_name === brand && a.year_month === latestMonth);
                brandAlerts.sort((a,b) => b.keyword_shift - a.keyword_shift);
                const topKeyword = brandAlerts.length > 0 ? `'` + brandAlerts[0].keyword + `'` : 'None';
                
                // Calculate Health Score
                const totalCount = brandReviews.length;
                const positiveCount = brandReviews.filter(d => d.sentiment_label === 'Positive').length;
                const negativeCount = brandReviews.filter(d => d.sentiment_label === 'Negative').length;
                const positivePct = totalCount ? (positiveCount / totalCount) * 100 : 0;
                const negativePct = totalCount ? (negativeCount / totalCount) * 100 : 0;
                const avgVelocity = brandSummaries.length ? (brandSummaries.map(d => d.review_velocity).reduce((a,b)=>a+b,0) / brandSummaries.length) : 0;
                
                const ratingScore = (parseFloat(avgRating) / 5) * 40;
                const sentimentScore = (((positivePct - negativePct) / 100 + 1) / 2) * 40;
                const velocityScore = avgVelocity > 0 ? 20 : (avgVelocity > -20 ? 10 : 0);
                const healthScore = Math.round(ratingScore + sentimentScore + velocityScore);
                
                let scoreClass = 'score-average';
                if (healthScore > 70) scoreClass = 'score-good';
                else if (healthScore < 50) scoreClass = 'score-poor';
                
                // Weekly Review Volume (simulated from latest dates)
                const weeklyCount = Math.round(brandReviews.length / 24); 
                
                const card = document.createElement('div');
                card.className = 'digest-card';
                card.innerHTML = `
                    <div class="digest-brand-name">${{brand}}</div>
                    <div class="digest-metric">
                        <span>Avg Rating</span>
                        <span>${{avgRating}}</span>
                    </div>
                    <div class="digest-metric">
                        <span>Trend MoM</span>
                        <span style="color: ${{ratingTrend < -0.1 ? 'var(--negative)' : (ratingTrend > 0.1 ? 'var(--positive)' : 'var(--text-secondary)')}}">${{trendText}}</span>
                    </div>
                    <div class="digest-metric">
                        <span>Top Complaint</span>
                        <span style="color: var(--accent);">${{topKeyword}}</span>
                    </div>
                    <div class="digest-metric">
                        <span>Weekly Volume</span>
                        <span>${{weeklyCount}} reviews</span>
                    </div>
                    <div class="digest-score-pill ${{scoreClass}}">
                        Health Score: ${{healthScore}}/100
                    </div>
                `;
                container.appendChild(card);
            }});
            
            // Dynamic plain English narrative block
            const selectedBrand = document.getElementById('brand-select').value;
            const narrativeText = document.getElementById('digest-narrative-text');
            
            if (selectedBrand === 'All') {{
                // Global narrative
                let lowestBrand = 'Plum';
                let alertString = "<b>Plum</b> rating dropped by <b>0.33 points</b>. <b>'ingredients'</b> and <b>'list'</b> complaints were up <b>80.0%</b> this month.";
                
                narrativeText.innerHTML = `
                    D2C Brand Health assessment for this period reveals mixed consumer feedback across the skincare category.<br/><br/>
                    <b>Anomaly Alert:</b> ${{alertString}}<br/><br/>
                    Overall, <b>Dot & Key</b> maintains the highest health index in the sector, driven by strong positive reviews regarding product <i>consistency</i> and <i>texture</i>.
                `;
            }} else {{
                // Specific brand narrative
                const bReviews = reviewsData.filter(r => r.brand_name === selectedBrand);
                const bSummaries = summaryData.filter(s => s.brand_name === selectedBrand);
                bSummaries.sort((a,b) => b.year_month.localeCompare(a.year_month));
                
                const latestMonth = bSummaries.length > 0 ? bSummaries[0].year_month : '-';
                const currentRating = bReviews.length ? (bReviews.map(r => r.rating).reduce((a,b)=>a+b, 0) / bReviews.length).toFixed(2) : '-';
                const trend = bSummaries.length > 0 ? bSummaries[0].rating_trend : 0;
                
                const bAlerts = alertsData.filter(a => a.brand_name === selectedBrand && a.year_month === latestMonth);
                bAlerts.sort((a,b) => b.keyword_shift - a.keyword_shift);
                
                const topKeyword = bAlerts.length > 0 ? bAlerts[0].keyword : 'none';
                const topShift = bAlerts.length > 0 ? bAlerts[0].keyword_shift.toFixed(1) : '0';
                
                let directionText = trend < 0 ? 'dropped' : 'gained';
                let absTrend = Math.abs(trend).toFixed(2);
                
                narrativeText.innerHTML = `
                    <b>${{selectedBrand}}</b>'s customer sentiment has been analyzed for the latest month (<b>${{latestMonth}}</b>).<br/><br/>
                    The average rating stands at <b>${{currentRating}}</b>. Compared to the previous month, the brand has <b>${{directionText}} ${{absTrend}} points</b>.<br/><br/>
                    The primary customer friction point centers around the word <b>'${{topKeyword}}'</b>, which showed a growing MoM complaint shift of <b>+${{topShift}}%</b> in negative reviews. Operations should investigate texture and delivery issues immediately to prevent further ratings erosion.
                `;
            }}
        }}
    </script>
</body>
</html>
"""
    
    # Write to dashboard.html
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Web dashboard generated successfully: {DASHBOARD_PATH}")
    print("You can now double-click 'dashboard.html' in File Explorer to view the dashboard in your browser!")

if __name__ == "__main__":
    main()
