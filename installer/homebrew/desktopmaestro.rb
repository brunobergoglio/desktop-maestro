# typed: false
# frozen_string_literal: true

# 🧹 DesktopMaestro – Homebrew Formula
# =============================================================================
# Instalación:
#   brew tap brunobergoglio/desktop-maestro
#   brew install desktopmaestro
#
# O directamente:
#   brew install brunobergoglio/desktop-maestro/desktopmaestro
# =============================================================================

class Desktopmaestro < Formula
  include Language::Python::Virtualenv

  desc "🧹 Organizador inteligente de escritorio para macOS"
  homepage "https://github.com/brunobergoglio/desktop-maestro"
  url "https://github.com/brunobergoglio/desktop-maestro/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"
  license "MIT"
  revision 1

  depends_on "python@3.12"

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/cd/e5/af35f7ea75cf72f2cd079c95ee16797de7cd71f29ea7c68ae5ce7be1eda0/PyYAML-6.0.2.tar.gz"
    sha256 "d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e"
  end

  def install
    virtualenv_install_with_resources
  end

  def post_install
    # Configuración por defecto
    config_dir = etc/"desktopmaestro"
    config_dir.mkpath unless config_dir.exist?

    # Logs
    log_dir = var/"log/desktopmaestro"
    log_dir.mkpath unless log_dir.exist?
  end

  def caveats
    <<~EOS
      🧹 DesktopMaestro instalado exitosamente!

      Comandos básicos:
        desktopmaestro organize --dry-run    # Simular organización
        desktopmaestro organize              # Organizar escritorio
        desktopmaestro stats                 # Ver estadísticas
        desktopmaestro --help                # Ayuda completa

      Para organización automática:
        desktopmaestro schedule enable --interval 6

      Nota: Si no puede acceder al escritorio, otorgale
      Acceso Total al Disco a tu terminal en:
        Preferencias del Sistema → Privacidad y Seguridad
    EOS
  end

  test do
    assert_match "v1.0.0", shell_output("#{bin}/desktopmaestro --version")
  end
end
