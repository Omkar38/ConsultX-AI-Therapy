import DashboardLayout from '@/features/dashboard/DashboardLayout'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useState } from 'react'

export const Route = createFileRoute('/dashboard')({
  component: DashboardLayout,
})