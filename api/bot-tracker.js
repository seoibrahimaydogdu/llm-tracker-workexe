app.use((req, res, next) => {
  const ua = req.headers['user-agent'] || '';
  const bots = ['Googlebot', 'GPTBot', 'ChatGPT', 'AhrefsBot', 'Bingbot', 'Yandex'];

  const foundBot = bots.find(bot => ua.includes(bot));
  if (foundBot) {
    fetch("https://your-project.supabase.co/rest/v1/bot_logs", {
      method: "POST",
      headers: {
        "apikey": "SUPABASE_API_KEY",
        "Authorization": "Bearer SUPABASE_API_KEY",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url: req.originalUrl,
        bot_name: foundBot,
        user_agent: ua,
        ip: req.headers['x-forwarded-for'] || req.socket.remoteAddress
      })
    });
  }

  next();
});