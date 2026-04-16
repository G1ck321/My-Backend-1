const express = require('express')
const { z } = require('zod')

const { publicSupabase, ensureSupabase } = require('../config/supabase')
const { signAccessToken, signRefreshToken, verifyToken } = require('../services/jwt.service')
const { authMiddleware } = require('../middleware/auth.middleware')

const authRouter = express.Router()

const signupSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  fullName: z.string().min(2),
  phoneNumber: z.string().min(7).optional(),
})

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

const profileUpdateSchema = z.object({
  fullName: z.string().min(2).optional(),
  phoneNumber: z.string().min(7).optional(),
})

authRouter.post('/signup', async (req, res, next) => {
  try {
    const payload = signupSchema.parse(req.body)

    if (!publicSupabase) {
      return res.status(503).json({
        success: false,
        message: 'Supabase auth is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY.',
      })
    }

    const { data, error } = await publicSupabase.auth.signUp({
      email: payload.email,
      password: payload.password,
      options: {
        data: {
          full_name: payload.fullName,
          phone_number: payload.phoneNumber || null,
        },
      },
    })

    if (error) {
      return res.status(400).json({ success: false, message: error.message })
    }

    if (data.user) {
      const adminSupabase = ensureSupabase()
      const { error: profileError } = await adminSupabase.from('profiles').upsert(
        {
          id: data.user.id,
          full_name: payload.fullName,
          phone_number: payload.phoneNumber || null,
          role: 'customer',
        },
        { onConflict: 'id' }
      )

      if (profileError) {
        return res.status(500).json({
          success: false,
          message: `User created but profile persistence failed: ${profileError.message}`,
        })
      }
    }

    const accessToken = signAccessToken(data.user.id, payload.email, 'customer')
    const refreshToken = signRefreshToken(data.user.id)

    return res.status(201).json({
      success: true,
      message: 'Signup successful.',
      data: {
        user: {
          id: data.user.id,
          email: data.user.email,
          fullName: payload.fullName,
        },
        accessToken,
        refreshToken,
        expiresIn: 86400,
      },
    })
  } catch (error) {
    return next(error)
  }
})

authRouter.post('/login', async (req, res, next) => {
  try {
    const payload = loginSchema.parse(req.body)

    if (!publicSupabase) {
      return res.status(503).json({
        success: false,
        message: 'Supabase auth is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY.',
      })
    }

    const { data, error } = await publicSupabase.auth.signInWithPassword({
      email: payload.email,
      password: payload.password,
    })

    if (error) {
      return res.status(401).json({ success: false, message: error.message })
    }

    let profile = null
    if (data.user) {
      try {
        const adminSupabase = ensureSupabase()
        const { data: profileData } = await adminSupabase
          .from('profiles')
          .select('id, full_name, phone_number, role, created_at, updated_at')
          .eq('id', data.user.id)
          .maybeSingle()
        profile = profileData
      } catch (profileError) {
        profile = null
      }
    }

    const accessToken = signAccessToken(data.user.id, payload.email, 'customer')
    const refreshToken = signRefreshToken(data.user.id)

    return res.status(200).json({
      success: true,
      message: 'Login successful.',
      data: {
        user: {
          id: data.user.id,
          email: data.user.email,
          fullName: profile?.full_name || data.user.user_metadata?.full_name || null,
        },
        accessToken,
        refreshToken,
        expiresIn: 86400,
        profile,
      },
    })
  } catch (error) {
    return next(error)
  }
})

authRouter.get('/profiles/:userId', async (req, res, next) => {
  try {
    const adminSupabase = ensureSupabase()
    const { data, error } = await adminSupabase
      .from('profiles')
      .select('id, full_name, phone_number, role, created_at, updated_at')
      .eq('id', req.params.userId)
      .maybeSingle()

    if (error) {
      return res.status(500).json({ success: false, message: error.message })
    }

    if (!data) {
      return res.status(404).json({ success: false, message: 'Profile not found.' })
    }

    return res.json({ success: true, data })
  } catch (error) {
    return next(error)
  }
})

authRouter.patch('/profiles/:userId', async (req, res, next) => {
  try {
    const payload = profileUpdateSchema.parse(req.body)
    const adminSupabase = ensureSupabase()
    const updatePayload = {}

    if (payload.fullName !== undefined) {
      updatePayload.full_name = payload.fullName
    }
    if (payload.phoneNumber !== undefined) {
      updatePayload.phone_number = payload.phoneNumber
    }
    updatePayload.updated_at = new Date().toISOString()

    const { data, error } = await adminSupabase
      .from('profiles')
      .update(updatePayload)
      .eq('id', req.params.userId)
      .select('id, full_name, phone_number, role, created_at, updated_at')
      .maybeSingle()

    if (error) {
      return res.status(500).json({ success: false, message: error.message })
    }

    if (!data) {
      return res.status(404).json({ success: false, message: 'Profile not found.' })
    }

    return res.json({ success: true, message: 'Profile updated.', data })
  } catch (error) {
    return next(error)
  }
})

authRouter.post('/refresh', async (req, res, next) => {
  try {
    const { refreshToken } = req.body

    if (!refreshToken) {
      return res.status(400).json({
        success: false,
        message: 'Refresh token is required.',
      })
    }

    const decoded = verifyToken(refreshToken)

    if (decoded.type !== 'refresh') {
      return res.status(401).json({
        success: false,
        message: 'Invalid refresh token.',
      })
    }

    const adminSupabase = ensureSupabase()
    const { data: profileData } = await adminSupabase
      .from('profiles')
      .select('full_name, role')
      .eq('id', decoded.sub)
      .maybeSingle()

    const newAccessToken = signAccessToken(
      decoded.sub,
      profileData?.email || 'unknown@example.com',
      profileData?.role || 'customer'
    )

    return res.json({
      success: true,
      data: {
        accessToken: newAccessToken,
        expiresIn: 86400,
      },
    })
  } catch (error) {
    return next(error)
  }
})

authRouter.post('/logout', (req, res) => {
  return res.json({
    success: true,
    message: 'Logout acknowledged. Clear tokens on client.',
  })
})

module.exports = { authRouter }