"""
AI-Powered Intelligence Module
- Demand Forecasting
- Smart Reordering Engine
- Dynamic Pricing Suggestions
- Stock Age Analysis
- Sales Pattern Recognition
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics


class AIDemandForecaster:
    """AI-powered demand forecasting using historical sales data"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        self.db_path = db_path
        
    def get_historical_sales(self, product_id: int, days: int = 90) -> List[Dict]:
        """Get historical sales data for a product"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        query = """
            SELECT so.order_date, soi.quantity, soi.unit_price
            FROM sales_order_items soi
            JOIN sales_orders so ON soi.order_id = so.id
            WHERE soi.product_id = ? AND so.order_date >= ?
            ORDER BY so.order_date DESC
        """
        
        cursor.execute(query, (product_id, cutoff_date))
        results = cursor.fetchall()
        conn.close()
        
        return [
            {"date": row[0], "quantity": row[1], "price": row[2]}
            for row in results
        ]
    
    def forecast_demand(self, product_id: int, forecast_days: int = 30) -> Dict[str, Any]:
        """Forecast demand for next N days using weighted moving average"""
        sales_data = self.get_historical_sales(product_id, days=90)
        
        if not sales_data:
            return {
                "predicted_demand": 0,
                "confidence": "low",
                "recommended_stock": 0,
                "trend": "insufficient_data"
            }
        
        # Group by day
        daily_sales = defaultdict(int)
        for sale in sales_data:
            daily_sales[sale["date"]] += sale["quantity"]
        
        if len(daily_sales) < 7:
            return {
                "predicted_demand": sum(daily_sales.values()),
                "confidence": "low",
                "recommended_stock": sum(daily_sales.values()) * 2,
                "trend": "limited_data"
            }
        
        # Calculate weighted moving average (recent days weighted more)
        values = list(daily_sales.values())
        weights = list(range(1, len(values) + 1))
        
        weighted_avg = sum(v * w for v, w in zip(values[-30:], weights[-30:])) / sum(weights[-30:])
        
        # Trend analysis
        recent_avg = statistics.mean(values[-7:]) if len(values) >= 7 else statistics.mean(values)
        older_avg = statistics.mean(values[:-7]) if len(values) > 7 else recent_avg
        
        if recent_avg > older_avg * 1.2:
            trend = "increasing"
            adjustment_factor = 1.3
        elif recent_avg < older_avg * 0.8:
            trend = "decreasing"
            adjustment_factor = 0.7
        else:
            trend = "stable"
            adjustment_factor = 1.0
        
        predicted_daily = weighted_avg * adjustment_factor
        predicted_total = predicted_daily * forecast_days
        
        # Confidence based on data consistency
        if len(values) >= 30:
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            cv = std_dev / statistics.mean(values) if statistics.mean(values) > 0 else 1
            confidence = "high" if cv < 0.3 else "medium" if cv < 0.6 else "low"
        else:
            confidence = "medium"
        
        return {
            "predicted_demand": round(predicted_total),
            "daily_average": round(predicted_daily, 2),
            "confidence": confidence,
            "recommended_stock": round(predicted_total * 1.2),  # 20% safety stock
            "trend": trend,
            "data_points": len(values)
        }
    
    def forecast_all_products(self, forecast_days: int = 30) -> List[Dict]:
        """Generate forecasts for all products"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, model, stock FROM products")
        products = cursor.fetchall()
        conn.close()
        
        forecasts = []
        for product_id, name, current_stock in products:
            forecast = self.forecast_demand(product_id, forecast_days)
            forecast["product_id"] = product_id
            forecast["product_name"] = name
            forecast["current_stock"] = current_stock
            
            # Calculate stockout risk
            if current_stock == 0:
                forecast["stockout_risk"] = "critical"
            elif current_stock < forecast["predicted_demand"] * 0.5:
                forecast["stockout_risk"] = "high"
            elif current_stock < forecast["predicted_demand"]:
                forecast["stockout_risk"] = "medium"
            else:
                forecast["stockout_risk"] = "low"
            
            forecasts.append(forecast)
        
        # Sort by stockout risk
        risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        forecasts.sort(key=lambda x: risk_order.get(x["stockout_risk"], 4))
        
        return forecasts


class SmartReorderEngine:
    """Intelligent purchase order suggestion engine"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        self.db_path = db_path
        self.forecaster = AIDemandForecaster(db_path)
    
    def analyze_reorder_needs(self) -> List[Dict[str, Any]]:
        """Analyze which products need reordering"""
        forecasts = self.forecaster.forecast_all_products(forecast_days=30)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        suggestions = []
        
        for forecast in forecasts:
            if forecast["stockout_risk"] in ["critical", "high", "medium"]:
                product_id = forecast["product_id"]
                
                # Get supplier info
                cursor.execute("""
                    SELECT p.supplier_id, s.name as supplier_name, 
                           p.purchase_price, p.min_stock
                    FROM products p
                    LEFT JOIN suppliers s ON p.supplier_id = s.id
                    WHERE p.id = ?
                """, (product_id,))
                
                result = cursor.fetchone()
                if result:
                    supplier_id, supplier_name, cost_price, min_stock = result
                    
                    reorder_qty = forecast["recommended_stock"] - forecast["current_stock"]
                    if reorder_qty < 0:
                        reorder_qty = 0
                    
                    estimated_cost = reorder_qty * (cost_price or 0)
                    
                    suggestions.append({
                        "product_id": product_id,
                        "product_name": forecast["product_name"],
                        "current_stock": forecast["current_stock"],
                        "predicted_demand": forecast["predicted_demand"],
                        "reorder_quantity": reorder_qty,
                        "supplier_id": supplier_id,
                        "supplier_name": supplier_name,
                        "estimated_cost": round(estimated_cost, 2),
                        "priority": "urgent" if forecast["stockout_risk"] == "critical" else 
                                   "high" if forecast["stockout_risk"] == "high" else "normal",
                        "confidence": forecast["confidence"],
                        "trend": forecast["trend"]
                    })
        
        conn.close()
        
        # Sort by priority
        priority_order = {"urgent": 0, "high": 1, "normal": 2}
        suggestions.sort(key=lambda x: (priority_order.get(x["priority"], 3), -x["predicted_demand"]))
        
        return suggestions
    
    def generate_auto_po(self, supplier_id: int = None) -> Dict[str, Any]:
        """Generate automatic purchase order for critical items"""
        suggestions = self.analyze_reorder_needs()
        
        if supplier_id:
            suggestions = [s for s in suggestions if s["supplier_id"] == supplier_id]
        
        if not suggestions:
            return None
        
        # Group by supplier
        supplier_items = defaultdict(list)
        for item in suggestions:
            supplier_items[item["supplier_id"]].append(item)
        
        pos = []
        for sup_id, items in supplier_items.items():
            po = {
                "supplier_id": sup_id,
                "supplier_name": items[0]["supplier_name"] if items else "Unknown",
                "items": items,
                "total_items": len(items),
                "total_quantity": sum(item["reorder_quantity"] for item in items),
                "estimated_total": sum(item["estimated_cost"] for item in items),
                "priority_count": {
                    "urgent": sum(1 for i in items if i["priority"] == "urgent"),
                    "high": sum(1 for i in items if i["priority"] == "high"),
                    "normal": sum(1 for i in items if i["priority"] == "normal")
                }
            }
            pos.append(po)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_pos": len(pos),
            "purchase_orders": pos
        }


class DynamicPricingAdvisor:
    """Dynamic pricing suggestions based on stock age and demand"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        self.db_path = db_path
    
    def get_aging_inventory(self, days_threshold: int = 90) -> List[Dict]:
        """Identify aging inventory that may need price adjustments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d')
        
        query = """
            SELECT p.id, p.model, p.stock, p.selling_price, p.purchase_price,
                   MIN(so.order_date) as last_sale_date,
                   julianday('now') - julianday(COALESCE(MIN(so.order_date), ?)) as days_since_sale
            FROM products p
            LEFT JOIN sales_order_items soi ON p.id = soi.product_id
            LEFT JOIN sales_orders so ON soi.order_id = so.id
            WHERE p.stock > 0
            GROUP BY p.id
            HAVING days_since_sale > ? OR last_sale_date IS NULL
            ORDER BY days_since_sale DESC
        """
        
        cursor.execute(query, (cutoff_date, days_threshold))
        results = cursor.fetchall()
        conn.close()
        
        recommendations = []
        for row in results:
            product_id, name, stock, sell_price, cost_price, last_sale, days_aging = row
            
            # Calculate margin
            margin = ((sell_price - cost_price) / sell_price * 100) if sell_price > 0 else 0
            
            # Suggest discount based on aging
            if days_aging > 180:
                suggested_discount = 25
                urgency = "critical"
            elif days_aging > 120:
                suggested_discount = 15
                urgency = "high"
            elif days_aging > 90:
                suggested_discount = 10
                urgency = "medium"
            else:
                suggested_discount = 5
                urgency = "low"
            
            new_price = sell_price * (1 - suggested_discount / 100)
            new_margin = ((new_price - cost_price) / new_price * 100) if new_price > 0 else 0
            
            recommendations.append({
                "product_id": product_id,
                "product_name": name,
                "current_stock": stock,
                "current_price": sell_price,
                "cost_price": cost_price,
                "current_margin": round(margin, 2),
                "days_since_last_sale": round(days_aging) if days_aging else None,
                "suggested_discount_percent": suggested_discount,
                "suggested_new_price": round(new_price, 2),
                "new_margin_percent": round(new_margin, 2),
                "urgency": urgency,
                "potential_loss": round((sell_price - new_price) * stock, 2)
            })
        
        return recommendations
    
    def get_optimal_pricing(self, product_id: int) -> Dict[str, Any]:
        """Get optimal pricing suggestion for a specific product"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get product info
        cursor.execute("""
            SELECT id, model, stock, selling_price, purchase_price, category_id
            FROM products WHERE id = ?
        """, (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return None
        
        # Get competitor pricing (simulated - would integrate with external API)
        # Get sales velocity
        cursor.execute("""
            SELECT COUNT(*) as total_sales, SUM(soi.quantity) as total_qty,
                   AVG(soi.unit_price) as avg_price
            FROM sales_order_items soi
            JOIN sales_orders so ON soi.order_id = so.id
            WHERE soi.product_id = ? AND so.order_date >= date('now', '-90 days')
        """, (product_id,))
        sales_stats = cursor.fetchone()
        
        conn.close()
        
        pid, name, stock, current_price, cost_price, category = product
        total_sales, total_qty, avg_sold_price = sales_stats
        
        # Calculate metrics
        margin = ((current_price - cost_price) / current_price * 100) if current_price > 0 else 0
        velocity = total_qty / 90 if total_qty else 0  # units per day
        
        # Pricing recommendation logic
        if velocity < 0.5 and stock > 10:  # Low velocity, high stock
            recommendation = "decrease"
            suggested_change = -10
            reason = "Low sales velocity suggests price is too high"
        elif velocity > 2 and stock < 20:  # High velocity, low stock
            recommendation = "increase"
            suggested_change = 8
            reason = "High demand allows for price optimization"
        elif margin < 15:  # Low margin
            recommendation = "review"
            suggested_change = 0
            reason = "Margin is below recommended 20% threshold"
        else:
            recommendation = "maintain"
            suggested_change = 0
            reason = "Current pricing is optimal"
        
        suggested_price = current_price * (1 + suggested_change / 100)
        
        return {
            "product_id": pid,
            "product_name": name,
            "current_price": current_price,
            "cost_price": cost_price,
            "current_margin_percent": round(margin, 2),
            "sales_velocity_daily": round(velocity, 2),
            "recommendation": recommendation,
            "suggested_change_percent": suggested_change,
            "suggested_price": round(suggested_price, 2),
            "reason": reason,
            "market_position": "competitive"  # Would be calculated from real market data
        }


class InventoryHealthAnalyzer:
    """Comprehensive inventory health analysis"""
    
    def __init__(self, db_path: str = "data/inventory.db"):
        self.db_path = db_path
        self.forecaster = AIDemandForecaster(db_path)
        self.pricing_advisor = DynamicPricingAdvisor(db_path)
    
    def get_health_score(self) -> Dict[str, Any]:
        """Calculate overall inventory health score (0-100)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get key metrics
        cursor.execute("SELECT COUNT(*) FROM products WHERE stock > 0")
        active_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE stock <= 0")
        out_of_stock = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM products 
            WHERE stock <= min_stock AND stock > 0
        """)
        low_stock = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(stock * purchase_price) FROM products")
        total_value = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(stock * selling_price) FROM products")
        total_retail_value = cursor.fetchone()[0] or 0
        
        conn.close()
        
        total_products = active_products + out_of_stock
        
        # Calculate component scores
        availability_score = max(0, 100 - (out_of_stock / max(total_products, 1) * 200))
        stock_balance_score = max(0, 100 - (low_stock / max(active_products, 1) * 150))
        
        # Get aging inventory impact
        aging_items = self.pricing_advisor.get_aging_inventory(days_threshold=90)
        aging_ratio = len(aging_items) / max(active_products, 1)
        freshness_score = max(0, 100 - (aging_ratio * 100))
        
        # Overall score (weighted average)
        overall_score = (
            availability_score * 0.4 +
            stock_balance_score * 0.3 +
            freshness_score * 0.3
        )
        
        # Determine health status
        if overall_score >= 80:
            status = "excellent"
            color = "#10B981"
        elif overall_score >= 60:
            status = "good"
            color = "#3B82F6"
        elif overall_score >= 40:
            status = "fair"
            color = "#F59E0B"
        else:
            status = "needs_attention"
            color = "#EF4444"
        
        return {
            "overall_score": round(overall_score),
            "status": status,
            "color": color,
            "components": {
                "availability": round(availability_score),
                "stock_balance": round(stock_balance_score),
                "freshness": round(freshness_score)
            },
            "metrics": {
                "total_products": total_products,
                "active_products": active_products,
                "out_of_stock": out_of_stock,
                "low_stock": low_stock,
                "total_inventory_value": round(total_value, 2),
                "total_retail_value": round(total_retail_value, 2),
                "aging_items_count": len(aging_items)
            },
            "recommendations": self._generate_recommendations(out_of_stock, low_stock, aging_items)
        }
    
    def _generate_recommendations(self, out_of_stock: int, low_stock: int, 
                                  aging_items: List) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        if out_of_stock > 0:
            recs.append(f"🚨 {out_of_stock} products are out of stock - create purchase orders immediately")
        
        if low_stock > 3:
            recs.append(f"⚠️ {low_stock} products are below minimum stock level")
        
        if len(aging_items) > 5:
            recs.append(f"💰 {len(aging_items)} products have aging inventory - consider promotions")
        
        if not recs:
            recs.append("✅ Inventory health is excellent - maintain current practices")
        
        return recs
