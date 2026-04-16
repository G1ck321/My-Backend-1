const express = require('express')
const { z } = require('zod')

const { authMiddleware } = require('../middleware/auth.middleware')
const { ensureSupabase } = require('../config/supabase')
const ordersRouter = express.Router()

const quoteSchema = z.object({
  isNewCustomer: z.boolean().default(false),
  deliveryLat: z.number(),
  deliveryLng: z.number(),
  zoneDiscountPercentage: z.number().min(0).max(100).default(0),
  items: z.array(
    z.object({
      name: z.string().min(1),
      quantity: z.number().int().positive(),
      unitPrice: z.number().nonnegative(),
    })
  ).min(1),
})

function calculateQuote(payload) {
  const subtotal = payload.items.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0)
  const newCustomerDiscount = payload.isNewCustomer ? subtotal * 0.1 : 0
  const locationDiscount = subtotal * (payload.zoneDiscountPercentage / 100)
  const discountTotal = newCustomerDiscount + locationDiscount
  const deliveryFee = subtotal >= 15000 ? 0 : 1500
  const total = Math.max(subtotal + deliveryFee - discountTotal, 0)

  return {
    subtotal,
    deliveryFee,
    newCustomerDiscount,
    locationDiscount,
    discountTotal,
    total,
  }
}

ordersRouter.post('/quote', authMiddleware, (req, res) => {
  const payload = quoteSchema.parse(req.body)

  return res.json({
    success: true,
    data: calculateQuote(payload),
  })
})

// POST /api/v1/orders - Create and persist order to Supabase
ordersRouter.post('/', authMiddleware, async (req, res) => {
  try {
    const payload = quoteSchema.parse(req.body)
    const quote = calculateQuote(payload)
    const supabase = ensureSupabase()

    // Create order in database
    const { data: orderData, error: orderError } = await supabase
      .from('orders')
      .insert([{
        customer_id: req.user.id,
        delivery_latitude: payload.deliveryLat,
        delivery_longitude: payload.deliveryLng,
        status: 'pending_payment',
        subtotal_amount: quote.subtotal,
        delivery_fee: quote.deliveryFee,
        discount_amount: quote.discountTotal,
        total_amount: quote.total,
        currency: 'NGN',
      }])
      .select()

    if (orderError) {
      return res.status(400).json({ success: false, message: orderError.message })
    }

    const orderId = orderData[0].id

    // Create order items
    const orderItems = payload.items.map(item => ({
      order_id: orderId,
      item_name: item.name,
      quantity: item.quantity,
      unit_price: item.unitPrice,
      line_total: item.quantity * item.unitPrice,
    }))

    const { error: itemsError } = await supabase
      .from('order_items')
      .insert(orderItems)

    if (itemsError) {
      return res.status(400).json({ success: false, message: itemsError.message })
    }

    return res.status(201).json({
      success: true,
      message: 'Order created successfully',
      data: {
        orderId,
        status: orderData[0].status,
        quote,
        createdAt: orderData[0].created_at,
      },
    })
  } catch (error) {
    if (error.name === 'ZodError') {
      return res.status(400).json({ success: false, errors: error.errors })
    }
    return res.status(500).json({ success: false, message: error.message })
  }
})

// GET /api/v1/orders/:userId - Get all orders for a user
ordersRouter.get('/:userId', authMiddleware, async (req, res) => {
  try {
    // Ensure user can only view their own orders
    if (req.user.id !== req.params.userId) {
      return res.status(403).json({ success: false, message: 'Unauthorized' })
    }

    const supabase = ensureSupabase()
    const { data, error } = await supabase
      .from('orders')
      .select(`
        id,
        status,
        subtotal_amount,
        delivery_fee,
        discount_amount,
        total_amount,
        created_at,
        updated_at,
        order_items(
          id,
          item_name,
          quantity,
          unit_price,
          line_total
        )
      `)
      .eq('customer_id', req.user.id)
      .order('created_at', { ascending: false })

    if (error) {
      return res.status(500).json({ success: false, message: error.message })
    }

    return res.json({
      success: true,
      data,
    })
  } catch (error) {
    return res.status(500).json({ success: false, message: error.message })
  }
})

// GET /api/v1/orders/:orderId/tracking - Track a single order
ordersRouter.get('/:orderId/tracking', authMiddleware, async (req, res) => {
  try {
    const supabase = ensureSupabase()
    const { data, error } = await supabase
      .from('orders')
      .select(`
        id,
        status,
        created_at,
        delivery_events(
          id,
          event_type,
          description,
          created_at,
          rider_location_lat,
          rider_location_lng
        )
      `)
      .eq('id', req.params.orderId)
      .eq('customer_id', req.user.id)
      .single()

    if (error) {
      return res.status(404).json({ success: false, message: 'Order not found' })
    }

    // Calculate ETA (for demo: preparation_time + 20min delivery)
    const createdAt = new Date(data.created_at)
    const eta = new Date(createdAt.getTime() + 35 * 60 * 1000)

    return res.json({
      success: true,
      data: {
        orderId: data.id,
        status: data.status,
        etaMinutes: Math.max(0, Math.round((eta - new Date()) / 60000)),
        liveTrackingEnabled: true,
        events: data.delivery_events || [],
      },
    })
  } catch (error) {
    return res.status(500).json({ success: false, message: error.message })
  }
})

module.exports = { ordersRouter }