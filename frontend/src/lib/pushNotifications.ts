export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) return false
  if (Notification.permission === 'granted') return true
  const result = await Notification.requestPermission()
  return result === 'granted'
}
export function sendNotification(title: string, body: string, icon?: string) {
  if (Notification.permission !== 'granted') return
  new Notification(title, { body, icon: icon || '/icon-192.png', badge: '/icon-192.png' })
}
