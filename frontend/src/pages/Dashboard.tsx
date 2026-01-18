import { Grid, Paper, Typography, Box, Card, CardContent } from '@mui/material'
import {
  TrendingUp as TrendingUpIcon,
  LocalShipping as LocalShippingIcon,
  Business as BusinessIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  color: string
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4">{value}</Typography>
          </Box>
          <Box
            sx={{
              backgroundColor: color,
              borderRadius: 2,
              padding: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export default function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        ダッシュボード
      </Typography>

      <Grid container spacing={3}>
        {/* 統計カード */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="稼働中の現場"
            value={5}
            icon={<BusinessIcon sx={{ color: 'white' }} />}
            color="#1976d2"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="稼働車両"
            value={23}
            icon={<LocalShippingIcon sx={{ color: 'white' }} />}
            color="#4caf50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="本日の運搬回数"
            value={148}
            icon={<TrendingUpIcon sx={{ color: 'white' }} />}
            color="#ff9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="アラート"
            value={3}
            icon={<WarningIcon sx={{ color: 'white' }} />}
            color="#f44336"
          />
        </Grid>

        {/* 地図エリア */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: 500 }}>
            <Typography variant="h6" gutterBottom>
              車両位置マップ
            </Typography>
            <Box
              sx={{
                height: 450,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f5f5f5',
                borderRadius: 1,
              }}
            >
              <Typography color="textSecondary">
                地図コンポーネントを実装予定
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* アラート一覧 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: 500 }}>
            <Typography variant="h6" gutterBottom>
              最新アラート
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography color="textSecondary" variant="body2">
                アラート表示を実装予定
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* 進捗グラフ */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              現場別進捗状況
            </Typography>
            <Box
              sx={{
                height: 350,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f5f5f5',
                borderRadius: 1,
              }}
            >
              <Typography color="textSecondary">
                進捗グラフを実装予定
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* サイクルタイム */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              平均サイクルタイム推移
            </Typography>
            <Box
              sx={{
                height: 350,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#f5f5f5',
                borderRadius: 1,
              }}
            >
              <Typography color="textSecondary">
                サイクルタイムグラフを実装予定
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
