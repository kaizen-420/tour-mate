function formatCurrency(value) {
  return 'Rs. ' + Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

async function updateEstimate() {
  if (!window.tourCostConfig) return;

  const payload = {
    base_price: window.tourCostConfig.basePrice,
    days: window.tourCostConfig.days,
    travelers: document.getElementById('travelers')?.value || 1,
    transport_choice: document.getElementById('transport_choice')?.value || 'Bus',
    hotel_choice: document.getElementById('hotel_choice')?.value || 'Standard',
    meal_plan: document.getElementById('meal_plan')?.value || 'Breakfast'
  };

  try {
    const response = await fetch('/api/cost-estimate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (data.error) return;
    const ids = {
      packageSub: data.package_subtotal,
      transportTotal: data.transport_total,
      hotelTotal: data.hotel_total,
      mealTotal: data.meal_total,
      discountTotal: data.discount,
      finalTotal: data.final_total
    };
    Object.entries(ids).forEach(([id, value]) => {
      const el = document.getElementById(id);
      if (el) el.textContent = formatCurrency(value);
    });
  } catch (error) {
    console.error('Estimate error:', error);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  ['travelers', 'transport_choice', 'hotel_choice', 'meal_plan'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', updateEstimate);
    if (el) el.addEventListener('input', updateEstimate);
  });
  updateEstimate();
});
