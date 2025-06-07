from src.models.base.application import aplicacion

from src.main import iniciar_n6
# from src.alt import iniciar


def main():
    """Inicializar el aplicativo."""

    aplicacion.profiler_habilitado = True
    # aplicacion.pagina_sample_network = "B"

    iniciar_n6()


if __name__ == "__main__":
    main()
