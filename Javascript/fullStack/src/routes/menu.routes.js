const express = require('express')
const { z } = require('zod')

const { ensureSupabase } = require('../config/supabase')
const { authMiddleware } = require('../middleware/auth.middleware')

const menuRouter = express.Router()

// Zod schema for creating menu items
const createMenuItemSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  price: z.number().positive('Price must be positive'),
  currency: z.string().default('NGN'),
  category: z.string().min(1, 'Category is required'),
  image_url: z.string().url().optional(),
  is_available: z.boolean().default(true),
  is_nigerian_snack: z.boolean().default(false),
  preparation_time_minutes: z.number().int().positive().default(15),
})

const sampleMenu = [
  {
    id: 'm1',
    name: 'Jollof Rice Special',
    category: 'main',
    price: 6500,
    currency: 'NGN',
    isAvailable: true,
  },
  {
    id: 'm2',
    name: 'Suya Wrap',
    category: 'snacks',
    price: 3500,
    currency: 'NGN',
    isAvailable: true,
  },
  {
    id: 'm3',
    name: 'Puff Puff Box',
    category: 'snacks',
    price: 2000,
    currency: 'NGN',
    isAvailable: true,
  },
]

// GET /api/v1/menu - Public endpoint to browse menu
menuRouter.get('/', async (req, res) => {
  try {
    const supabase = ensureSupabase()
    const { data, error } = await supabase
      .from('menu_items')
      .select('id, name, description, price, currency, image_url, is_available, is_nigerian_snack, preparation_time_minutes')
      .eq('is_available', true)
      .order('created_at', { ascending: false })

    if (error) {
      return res.status(500).json({ success: false, message: error.message })
    }

    return res.json({
      success: true,
      data: data.length > 0 ? data : sampleMenu,
    })
  } catch (error) {
    return res.json({
      success: true,
      data: sampleMenu,
      note: 'Supabase not configured yet, returning starter sample menu.',
    })
  }
})

// POST /api/v1/menu - Admin endpoint to create menu items (requires auth)
menuRouter.post('/', authMiddleware, async (req, res) => {
  try {
    const payload = createMenuItemSchema.parse(req.body)
    const supabase = ensureSupabase()

    const { data, error } = await supabase
      .from('menu_items')
      .insert([{
        name: payload.name,
        description: payload.description,
        price: payload.price,
        currency: payload.currency,
        category: payload.category,
        image_url: payload.image_url,
        is_available: payload.is_available,
        is_nigerian_snack: payload.is_nigerian_snack,
        preparation_time_minutes: payload.preparation_time_minutes,
      }])
      .select()

    if (error) {
      return res.status(400).json({ success: false, message: error.message })
    }

    return res.status(201).json({
      success: true,
      message: 'Menu item created successfully',
      data: data[0],
    })
  } catch (error) {
    if (error.name === 'ZodError') {
      return res.status(400).json({ success: false, errors: error.errors })
    }
    return res.status(500).json({ success: false, message: error.message })
  }
})

module.exports = { menuRouter }