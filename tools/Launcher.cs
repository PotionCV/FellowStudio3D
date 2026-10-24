using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class Launcher
{
    [STAThread]
    private static int Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        try
        {
            string python = null;
            foreach (string relative in new[] { @"runtime\pythonw.exe", @".venv\Scripts\pythonw.exe" })
            {
                string candidate = Path.Combine(root, relative);
                if (File.Exists(candidate)) { python = candidate; break; }
            }
            if (python == null)
                foreach (string folder in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(';'))
                {
                    if (String.IsNullOrWhiteSpace(folder)) continue;
                    string candidate = Path.Combine(folder.Trim().Trim('"'), "pythonw.exe");
                    if (File.Exists(candidate)) { python = candidate; break; }
                }
            if (python == null)
                throw new FileNotFoundException("Python runtime is missing. Please extract the complete Windows portable package beside FellowStudio3D.exe.");
            string script = Path.Combine(root, "launch.py");
            if (!File.Exists(script)) throw new FileNotFoundException("launch.py is missing. Please extract the complete package.");
            var start = new ProcessStartInfo(python, "-I \"" + script + "\"");
            start.WorkingDirectory = root;
            start.UseShellExecute = false;
            start.CreateNoWindow = true;
            Process.Start(start);
            return 0;
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "FellowStudio3D", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
