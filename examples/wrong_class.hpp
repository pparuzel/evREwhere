
namespace evre
{

template <typename T>
class Widget
{
	Widget<T>() = default;

	void foo();
	void bar();
};

template <typename T>
void evre::Widget<T>::foo()
{
}

template <typename T>
void evre::Widget<T>::bar()
{
}

}  // namespace evre
