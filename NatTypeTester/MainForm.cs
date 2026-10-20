using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Threading.Tasks;
using System.Windows.Forms;
using LumiSoft.Net.STUN.Client;

namespace NatTypeTester
{
	public partial class MainForm : Form
	{
		public MainForm()
		{
			InitializeComponent();
		}

		private delegate void VoidMethodDelegate();

		/// <summary>
		/// 把异常写进 %TEMP%\NatTypeTester_error.log，并把日志路径告诉用户。
		/// 界面上只显示人能看懂的一段话，而不是一整坨 StackTrace。
		/// </summary>
		private static void ReportException(string caption, string friendlyMessage, Exception ex)
		{
			string logPath;
			try
			{
				logPath = Path.Combine(Path.GetTempPath(), "NatTypeTester_error.log");
				File.AppendAllText(
					logPath,
					$"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {caption}{Environment.NewLine}{ex}{Environment.NewLine}{Environment.NewLine}");
			}
			catch
			{
				logPath = null;
			}

			var text = friendlyMessage;
			if (!string.IsNullOrEmpty(logPath))
			{
				text += Environment.NewLine + Environment.NewLine + @"详细信息已写入日志：" + Environment.NewLine + logPath;
			}

			MessageBox.Show(text, caption, MessageBoxButtons.OK, MessageBoxIcon.Warning);
		}

		/// <summary>
		/// 把 SocketException 翻译成看得懂的提示。
		/// </summary>
		private static string DescribeSocketError(SocketException ex, string server, int port)
		{
			switch (ex.SocketErrorCode)
			{
				case SocketError.HostNotFound:
				case SocketError.NoData:
					return $@"无法解析 STUN 服务器域名：{server}

该域名在公共 DNS 里查不到（NXDOMAIN），说明这个 STUN 服务已经下线，
或者域名已过期被回收，不是本机网络的问题。

可以这样处理：
1. 检查域名是否拼写正确；
2. 换一个可用的服务器，例如 stun.miwifi.com、stun.hitv.com。";

				case SocketError.TryAgain:
					return $@"DNS 暂时无法解析 {server}。

这是本机 DNS 服务器的临时故障，稍等几秒再试一次。";

				case SocketError.TimedOut:
					return $@"连接 STUN 服务器超时：{server}:{port}

可能的原因：
1. 该服务器已停止服务，或 {port}/UDP 被防火墙拦了；
2. 本机网络或代理禁止 UDP 出网。

换一个服务器，或换一条网络再试。";

				case SocketError.NetworkUnreachable:
				case SocketError.HostUnreachable:
					return $@"网络不可达：{server}:{port}

请检查本机网络连接（或 VPN / 代理）是否正常。";

				case SocketError.ConnectionRefused:
					return $@"{server}:{port} 拒绝连接。

服务器的 {port} 端口没有在监听，多半是 STUN 服务已关闭。";

				default:
					return $@"连接 STUN 服务器失败：{server}:{port}

错误代码：{ex.SocketErrorCode}（{(int)ex.SocketErrorCode}）";
			}
		}

		private static string[] Core(string local, string server, int port)
		{
			try
			{
				if (string.IsNullOrWhiteSpace(server))
				{
					MessageBox.Show(@"Please specify STUN server !", @"Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
					return null;
				}

				using (var socketv4 = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp))
				{
					if (local != string.Empty)
					{
						var ip_port = local.Split(':');
						socketv4.Bind(new IPEndPoint(IPAddress.Parse(ip_port[0]), Convert.ToInt32(ip_port[1])));
					}
					else
					{
						socketv4.Bind(new IPEndPoint(IPAddress.Any, 0));
					}

					var result = STUN_Client.Query(server, port, socketv4);

					return new[]
					{
							result.NetType.ToString(),
							socketv4.LocalEndPoint.ToString(),
							result.NetType != STUN_NetType.UdpBlocked ? result.PublicEndPoint.ToString() : string.Empty
					};
				}
			}
			catch (SocketException ex)
			{
				// 域名不存在 / 超时 / 不可达 —— 都是很常见的用户输入问题，
				// 不该拿一坨异常堆栈糊到用户脸上。
				ReportException(@"STUN 测试失败", DescribeSocketError(ex, server, port), ex);
				return null;
			}
			catch (FormatException ex)
			{
				ReportException(
					@"本地地址格式错误",
					$@"本地地址 “{local}” 格式不对。

正确写法是 IP:端口，例如 0.0.0.0:0 或 192.168.1.10:5000。",
					ex);
				return null;
			}
			catch (Exception ex)
			{
				ReportException(
					@"STUN 测试失败",
					$@"与 STUN 服务器 {server}:{port} 通信时出错：{ex.Message}

请确认服务器地址和端口是否正确，或换一个服务器再试。",
					ex);
				return null;
			}
		}

		private void button1_Click(object sender, EventArgs e)
		{
			try
			{
				button1.Enabled = false;
				textBox2.Text = string.Empty;
				textBox4.Text = string.Empty;
				var server = comboBox1.Text.Trim();
				var port = Convert.ToInt32(numericUpDown1.Value);
				var local = textBox3.Text.Trim();
				string[] res = null;
				var t = new Task(() =>
				{
					res = Core(local, server, port);
				});
				t.Start();
				t.ContinueWith(task =>
				{
					BeginInvoke(new VoidMethodDelegate(() =>
					{
						if (res != null)
						{
							textBox2.Text = res[0];
							textBox3.Text = res[1];
							textBox4.Text = res[2];
						}
						button1.Enabled = true;
					}));
				});
			}
			catch (Exception ex)
			{
				ReportException(@"STUN 测试失败", $@"启动测试时出错：{ex.Message}", ex);
				button1.Enabled = true;
			}
		}

		private void MainForm_Load(object sender, EventArgs e)
		{
			comboBox1.SelectedIndex = 0;
		}
	}
}
