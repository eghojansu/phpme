<?php

class Command
{
    public function run($command, array $commandArgs = null)
    {
        return $this->doRun(trim($command), (array) $commandArgs);
    }

    public function doRun($command, array $args)
    {
        $method = static::normalizeCommand($command);
        if (method_exists($this, $method)) {
            return $this->$method($args);
        }

        return sprintf('error: Command "%s" not found', $command);
    }

    private function _commandInterfaceMethods(array $namespaces)
    {
        $namespace = array_shift($namespaces);
        if (!$namespace) {
            return 'error: No namespace given';
        }

        return $this->parseClass($namespace, function($ref) {
            return $ref->isInterface();
        }, sprintf('error: Namespace was not an interface (%s)', $namespace));
    }

    private function _commandClassMethods(array $namespaces)
    {
        $namespace = array_shift($namespaces);
        if (!$namespace) {
            return 'error: No namespace given';
        }

        return $this->parseClass($namespace);
    }

    private function _commandClasses(array $symbols)
    {
        return json_encode(array_values(array_intersect(array_merge(get_declared_classes(), get_declared_interfaces()), $symbols)));
    }

    private function parseClass($namespace, $validate = null, $message = null)
    {
        try {
            $ref = new ReflectionClass($namespace);
            if ($validate && !$validate($ref)) {
                return $message;
            }

            $methods = [];
            foreach ($ref->getMethods() as $key => $method) {
                $line = $this->methodLine($method);
                $methods[$method->name] = [
                    'def' => $line[0],
                    'uses' => $line[1] ?: false,
                    'docblocks' => $method->getDocComment()
                ];
            }

            return json_encode($methods);
        } catch (Exception $e) {
            return sprintf('error: Unexpected (%s)', $e->getMessage());
        }
    }

    private function methodLine(ReflectionMethod $method)
    {
        $modifiers = Reflection::getModifierNames($method->getModifiers());
        $modifier_str = trim(str_replace('abstract', '', implode(' ', $modifiers)));
        $args = '';
        $uses = [];
        foreach ($method->getParameters() as $key => $parameter) {
            $line = $this->parameterLine($parameter);
            $uses = array_merge($uses, $line[1]);
            $args .= ($args?', ':'').$line[0];
        }
        $uses = array_unique($uses);

        return [
            trim(sprintf('%s function %s(%s)', $modifier_str, $method->name, $args)),
            array_combine($uses, $uses),
        ];
    }

    private function parameterLine(ReflectionParameter $parameter)
    {
        $uses = [];
        $line = [];
        if ($parameter->hasType()) {
            $line[] = (string) $parameter->getType();
        } elseif ($class = $parameter->getClass()) {
            $line[] = $class->name;
            $uses[] = $class->name;
        }
        $line[] = '$'.$parameter->name;
        if ($parameter->isDefaultValueAvailable()) {
            if ($parameter->isDefaultValueConstant()) {
                $line[] = $parameter->getDefaultValueConstantName();
            } else {
                $line[] = $parameter->getDefaultValue();
            }
        }

        return [
            implode(' ', $line),
            $uses,
        ];
    }

    private static function normalizeCommand($command)
    {
        return '_command'.str_replace(' ', '', ucwords(str_replace('-', ' ', trim($command, '-'))));
    }
}
